#!/usr/bin/env python3
"""
scan.py — Token 体检的唯一扫描器。单次遍历日志，产出 facts.json。

设计原则（来自一次真实审计的教训）：
  1. **口径唯一。** "什么算一轮""什么算上下文""排不排子 agent" 只在本文件定义一次。
     早先的版本把这些散在 12 个脚本里，彼此不一致，导致一份报告漏计 42% 的轮次而无人察觉。
  2. **不判断，只测量。** 本文件不产出任何"健康/退化/浪费"的判断。
     阈值由用户设定，叙事由 narrative-rules.md 约束。
  3. **单次遍历。** 日志可达数 GB，每个指标各扫一遍既慢又容易口径漂移。

用法：
    python3 scan.py [-o facts.json]
    AUDIT_SINCE=2026-01-01 AUDIT_UNTIL=2026-06-30 python3 scan.py   # 限定窗口
"""
import argparse, json, glob, os, re, statistics as st, subprocess, sys
from collections import defaultdict, Counter
from datetime import datetime, timezone

SCHEMA_VERSION = 2

# ─────────────────────────── 口径：只在这里定义一次 ───────────────────────────
SINCE = os.environ.get('AUDIT_SINCE', '0000-00-00')
UNTIL = os.environ.get('AUDIT_UNTIL', '9999-99-99')

# 相对价格权重。仅用于"成本占比"，不换算成货币——各家定价会变，且订阅制下不等于账单。
W = {'input': 1.0, 'cache_write': 1.25, 'cache_read': 0.1, 'output': 5.0}

LATENCY_CAP_S = 600          # 超过视为人离开/断网，剔除
MIN_BIN = 40                 # 分层统计的最小样本量，不足则不输出该格

# 注入内容：这些不是人打的字，测"提示质量"时必须剔除
INJECTED_PREFIXES = (
    'Base directory for this skill:', '<system-reminder', '<command-', '<local-command',
    '<user-prompt-submit-hook', 'Caveat: The messages below', '[Request interrupted',
    '<bash-', '<task-notification', '<function_results',
)
CORRECTION_MARKERS = ['不对', '不是这', '错了', '搞错', '弄错', '重新', '再来一', '我是说',
                      '应该是', '不行', '还是不', '改回', '撤销', 'revert', '不该',
                      '我的意思是', '你理解错', '不要这样', '重做']
TEMP_MARKS = ('/tmp', '/private/tmp', '/var/folders', 'scratchpad',
              '/Downloads', '/Desktop', '/private/var')

CTX_BINS = [(0, 100_000, '<100K'), (100_000, 250_000, '100-250K'), (250_000, 10**18, '>250K')]
OUT_BINS = [(0, 200, '<200'), (200, 600, '200-600'), (600, 1500, '600-1.5K'), (1500, 10**18, '>1.5K')]
CTX_CURVE = [(0, 50_000, '<50K'), (50_000, 100_000, '50-100K'), (100_000, 150_000, '100-150K'),
             (150_000, 200_000, '150-200K'), (200_000, 300_000, '200-300K'),
             (300_000, 500_000, '300-500K'), (500_000, 10**18, '>500K')]

HOME = os.path.expanduser('~')


def in_window(ts10):
    return SINCE <= ts10 <= UNTIL


def parse_ts(ts):
    try:
        return datetime.fromisoformat((ts or '').replace('Z', '+00:00'))
    except Exception:
        return None


def pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(int(len(s) * q), len(s) - 1)]


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** .5
    return round(cov / den, 3) if den else None


def slope(xs, ys):
    if len(xs) < 3:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    den = sum((a - mx) ** 2 for a in xs)
    return round(sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / den, 1) if den else None


def human_text(msg):
    """返回人真正打的字；注入内容与工具结果返回空串。"""
    c = (msg or {}).get('content')
    if isinstance(c, str):
        t = c
    elif isinstance(c, list):
        if any(isinstance(b, dict) and b.get('type') == 'tool_result' for b in c):
            return ''
        t = ' '.join(b.get('text', '') for b in c if isinstance(b, dict) and b.get('type') == 'text')
    else:
        return ''
    t = t.strip()
    if not t or t.startswith(INJECTED_PREFIXES):
        return ''
    return re.sub(r'<system-reminder>.*?</system-reminder>', '', t, flags=re.S).strip()


def project_of(cwd):
    """项目名 = 工作目录的最后一段；家目录根单列。不硬编码任何人的项目名。"""
    c = (cwd or '').rstrip('/')
    if not c:
        return '(未知)'
    if c == HOME:
        return '~ (家目录根)'
    rel = c.replace(HOME, '~')
    parts = [p for p in rel.split('/') if p and p != '~']
    if not parts:
        return '~ (家目录根)'
    # ~/Project/foo/bar → foo；~/foo → foo
    return parts[1] if len(parts) > 1 and parts[0] in ('Project', 'Projects', 'code', 'src', 'work') else parts[0]


# ─────────────────────────── Claude Code ───────────────────────────
def scan_claude(state):
    files = glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'), recursive=True)
    state['scan']['claude_files'] = len(files)
    for fp in files:
        try:
            prev_t = None
            for line in open(fp, encoding='utf-8', errors='ignore'):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                ts = d.get('timestamp') or ''
                t = parse_ts(ts)
                typ = d.get('type')
                sid = d.get('sessionId') or fp
                cwd = d.get('cwd') or ''

                if not in_window(ts[:10]):
                    if t:
                        prev_t = t
                    continue

                # ── 用户消息：提示质量（人打的字才算）
                # ⚠ 必须与 assistant 分支一样排除 sidechain：
                #   tool_use 计数只统计主对话，若这里把子 agent 的 tool_result 错误也算进来，
                #   分子分母口径不一致，失败率会被系统性抬高（实测由 2.83% 虚增到 3.68%）。
                if typ == 'user' and not d.get('isSidechain'):
                    txt = human_text(d.get('message'))
                    if txt:
                        s = state['human'][sid]
                        s['cwd'] = s['cwd'] or cwd
                        if not s['msgs']:
                            # 开场白签名：压掉空白后取前 200 字，用于识别程序化模板
                            s['first_sig'] = re.sub(r'\s+', ' ', txt)[:200]
                        s['msgs'].append(len(txt))
                        if any(k in txt for k in CORRECTION_MARKERS):
                            state['corrections'] += 1
                        state['user_msgs'] += 1
                    c = (d.get('message') or {}).get('content')
                    if isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get('type') == 'tool_result':
                                nm = state['tool_of'].get(b.get('tool_use_id'), '?')
                                if b.get('is_error'):
                                    state['tool_err'][nm] += 1
                    if t:
                        prev_t = t
                    continue

                if typ != 'assistant':
                    if t:
                        prev_t = t
                    continue

                msg = d.get('message') or {}
                u = msg.get('usage')
                if not isinstance(u, dict):
                    if t:
                        prev_t = t
                    continue

                inp = u.get('input_tokens', 0) or 0
                cw = u.get('cache_creation_input_tokens', 0) or 0
                cr = u.get('cache_read_input_tokens', 0) or 0
                out = u.get('output_tokens', 0) or 0
                ctx = inp + cw + cr

                if d.get('isSidechain'):
                    state['sidechain']['turns'] += 1
                    state['sidechain']['ctx'].append(ctx)
                    if t:
                        prev_t = t
                    continue

                # ── 主对话轮次
                state['tok']['input'] += inp
                state['tok']['cache_write'] += cw
                state['tok']['cache_read'] += cr
                state['tok']['output'] += out
                state['turns'] += 1
                state['ctx_all'].append(ctx)
                state['by_month'][ts[:7]].append(ctx)
                state['sessions'][sid].append(ctx)
                state['sess_cwd'].setdefault(sid, cwd)
                state['sess_model'][sid].add((msg.get('model') or '?'))

                # ⚠ 成本必须四分量全权重。曾有一版写成 ctx×0.1 + out×5，
                #   把 input(1.0) 和 cache_write(1.25) 都按 0.1 计了——cache_write 单价是
                #   read 的 12.5 倍，命中率 97% 时其加权成本约为 read 的 40%，不可忽略；
                #   且 cost_pct 分母是全口径，分子是简化口径，各项目加总不到 100%。
                turn_cost = (inp * W['input'] + cw * W['cache_write']
                             + cr * W['cache_read'] + out * W['output'])

                p = project_of(cwd)
                pr = state['projects'][p]
                pr['turns'] += 1
                pr['ctx'].append(ctx)
                pr['cost'] += turn_cost
                pr['sessions'].add(sid)
                pr['seq'].append((len(state['sessions'][sid]) - 1, ctx))

                state['cwd_cost'][cwd] += turn_cost

                if prev_t and t:
                    dur = (t - prev_t).total_seconds()
                    if 0 < dur <= LATENCY_CAP_S:
                        state['lat'].append((ctx, out, dur))
                        state['wait_s'] += dur
                    elif dur > LATENCY_CAP_S:
                        state['lat_dropped'] += 1

                for b in msg.get('content') or []:
                    if isinstance(b, dict) and b.get('type') == 'tool_use':
                        nm = b.get('name', '?')
                        state['tool_of'][b.get('id')] = nm
                        state['tool_calls'][nm] += 1
                        fpath = (b.get('input') or {}).get('file_path')
                        if fpath and nm in ('Edit', 'Write', 'NotebookEdit'):
                            state['edits'][sid][fpath] += 1

                if d.get('isCompactSummary'):
                    pass
                if t:
                    prev_t = t

            # compact 事件：单独一遍轻量扫（需要前后上下文配对）
            # ⚠ 手动/自动的判定必须读 compact_boundary 的 compactMetadata.trigger（权威字段）。
            #   曾用「摘要文本含 'ran out of context' → auto」来猜——实际上手动与自动的
            #   续接摘要都含这句话，导致 19 次 compact 被 100% 误判为自动
            #   （权威字段实测：14 手动 + 5 自动），并由此产出「主动 compact 0 次」的假结论。
            #   教训：有权威字段就不许用字符串猜（「没核实字段语义」的二次复发）。
            seq = []
            for line in open(fp, encoding='utf-8', errors='ignore'):
                if '"compact_boundary"' not in line and '"assistant"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if not in_window((d.get('timestamp') or '')[:10]):
                    continue
                meta = d.get('compactMetadata')
                if d.get('subtype') == 'compact_boundary' and isinstance(meta, dict) \
                        and meta.get('trigger'):
                    # 会话 resume 会把历史行复制进新文件 → 必须跨文件去重
                    key = (d.get('timestamp'), meta.get('trigger'), meta.get('preTokens'))
                    if key in state['compact_seen']:
                        continue
                    state['compact_seen'].add(key)
                    trig = meta['trigger'] if meta['trigger'] in ('auto', 'manual') else 'other'
                    seq.append(('C', trig))
                    if meta.get('preTokens') and trig != 'other':
                        state['compact_pre'][trig].append(meta['preTokens'])
                elif d.get('type') == 'assistant' and not d.get('isSidechain'):
                    u = (d.get('message') or {}).get('usage')
                    if isinstance(u, dict):
                        seq.append(('A', (u.get('input_tokens', 0) or 0)
                                    + (u.get('cache_creation_input_tokens', 0) or 0)
                                    + (u.get('cache_read_input_tokens', 0) or 0)))
            for i, (k, v) in enumerate(seq):
                if k != 'C':
                    continue
                state['compact'][v] += 1
                before = next((seq[j][1] for j in range(i - 1, -1, -1) if seq[j][0] == 'A'), None)
                after = next((seq[j][1] for j in range(i + 1, len(seq)) if seq[j][0] == 'A'), None)
                if before:
                    state['compact_before'].append(before)
                if after:
                    state['compact_after'].append(after)
        except Exception:
            state['scan']['read_errors'] += 1


# ─────────────────────────── Codex ───────────────────────────
def scan_codex(state):
    """Codex 的 rollout 格式一直在变，且分「累计」与「本轮」两套用量，混加会重复计数。
    这里只取每个会话最后一条累计值，并显式记录用的是哪种字段。"""
    files = glob.glob(os.path.expanduser('~/.codex/sessions/**/rollout-*.jsonl'), recursive=True)
    if not files:
        return None
    cx = {'files': len(files), 'sessions': 0, 'turns': 0,
          'input': 0, 'cached_input': 0, 'output': 0, 'reasoning': 0,
          'ctx': [], 'field_source': None}
    for fp in files:
        try:
            last_total, turns, ctxs = None, 0, []
            for line in open(fp, encoding='utf-8', errors='ignore'):
                if 'token' not in line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if not in_window((d.get('timestamp') or '')[:10]):
                    continue
                pay = d.get('payload') or d
                info = pay.get('info') or pay
                tot = info.get('total_token_usage') or info.get('total') or None
                lastu = info.get('last_token_usage') or None
                if isinstance(tot, dict):
                    last_total = tot
                    cx['field_source'] = 'total_token_usage(取会话最后一条)'
                if isinstance(lastu, dict):
                    turns += 1
                    c = (lastu.get('input_tokens', 0) or 0) + (lastu.get('cached_input_tokens', 0) or 0)
                    if c:
                        ctxs.append(c)
            if last_total:
                cx['sessions'] += 1
                cx['turns'] += turns
                cx['input'] += last_total.get('input_tokens', 0) or 0
                cx['cached_input'] += last_total.get('cached_input_tokens', 0) or 0
                cx['output'] += last_total.get('output_tokens', 0) or 0
                cx['reasoning'] += last_total.get('reasoning_output_tokens', 0) or 0
                cx['ctx'].extend(ctxs)
        except Exception:
            pass
    if not cx['sessions']:
        return None
    ctxs = cx.pop('ctx')
    cx['avg_ctx'] = round(st.mean(ctxs)) if ctxs else None
    cx['p90_ctx'] = pct(ctxs, .9)
    cx['note'] = ('不折算货币：缺少权威的第三方定价，宁可不写。'
                  '与 Claude Code 的加权成本不可直接相比（权重体系不同）。')
    return cx


# ─────────────────────────── 汇总 ───────────────────────────
def build_facts(state, codex):
    f = {}
    tok = state['tok']
    cost = {k: tok[k] * W[k] for k in tok}
    total_cost = sum(cost.values()) or 1

    f['schema_version'] = SCHEMA_VERSION
    f['meta'] = {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'window': {'since': SINCE, 'until': UNTIL},
        'weights': W,
        'weights_note': '相对权重，仅用于成本占比；不换算货币（定价会变，订阅制下也不等于账单）。',
    }
    f['scan'] = dict(state['scan'],
                     sessions=len(state['sessions']),
                     main_turns=state['turns'],
                     sidechain_turns=state['sidechain']['turns'],
                     human_sessions=None,  # 见 prompt_quality.human_sessions（已剔除程序化会话）
                     user_messages=state['user_msgs'])

    # 成本构成
    f['cost'] = {
        'by_kind': {k: {'tokens': tok[k], 'cost_pct': round(cost[k] / total_cost * 100, 1)} for k in tok},
        'cache_hit_rate_pct': round(tok['cache_read'] / max(tok['cache_read'] + tok['cache_write'], 1) * 100, 1),
    }

    # 结构性下限 = 地基 × 轮数。地基取会话内最小非零上下文。
    # ⚠ 注意：曾有一版把"首轮"当地基，但因时间戳只精确到日期，排序后取到的是
    #   "当天最小的一轮"而非真正首轮，把下限压低了约 2.7 个百分点。
    #   完整时间戳下，"首轮"与"最小非零"结果一致——两者不是独立口径，不要当成区间报。
    act = flo = 0
    for sid, ctxs in state['sessions'].items():
        if len(ctxs) < 2:
            continue
        act += sum(ctxs)
        flo += min([x for x in ctxs if x > 0], default=0) * len(ctxs)
    sp = flo / act * 100 if act else 0
    f['floor'] = {
        'structural_pct': round(sp, 1),
        'behavioral_pct': round(100 - sp, 1),
        'method': '地基（会话内最小非零上下文）× 轮数 ÷ 实际重读总量。',
        'caveat': ('behavioral_pct 是可压缩量的**上界**，不是可省收益：'
                   '真开新对话要重新交代背景、重读文件，实际能省的更少。'
                   '这是会计恒等式，不是因果估计。'),
    }

    # 上下文分布
    ctxs = state['ctx_all']
    f['context'] = {
        'p25': pct(ctxs, .25), 'p50': pct(ctxs, .5), 'p75': pct(ctxs, .75),
        'p90': pct(ctxs, .9), 'p99': pct(ctxs, .99), 'mean': round(st.mean(ctxs)) if ctxs else None,
        'by_month': {m: {'turns': len(v), 'median': pct(v, .5)}
                     for m, v in sorted(state['by_month'].items()) if len(v) >= 50},
        'by_month_caveat': '月度对比会被"当月在做什么项目"混淆，不足以判断进步或退步。',
    }

    # 延迟：未控制 + 控制输出长度
    lat = state['lat']
    curve = []
    for lo_, hi_, lb in CTX_CURVE:
        v = [s for c, o, s in lat if lo_ <= c < hi_]
        if len(v) >= MIN_BIN:
            curve.append({'bin': lb, 'n': len(v), 'median_s': round(st.median(v), 1),
                          'p90_s': round(pct(v, .9), 1)})
    grid = []
    for olo, ohi, olb in OUT_BINS:
        row = {'output_bin': olb, 'cells': []}
        for clo, chi, clb in CTX_BINS:
            v = [s for c, o, s in lat if olo <= o < ohi and clo <= c < chi]
            row['cells'].append({'ctx_bin': clb, 'n': len(v),
                                 'median_s': round(st.median(v), 1) if len(v) >= MIN_BIN else None})
        meds = [c['median_s'] for c in row['cells']]
        row['amplification'] = (round(meds[-1] / meds[0], 2)
                                if meds and meds[0] and meds[-1] else None)
        grid.append(row)
    f['latency'] = {
        'total_wait_hours': round(state['wait_s'] / 3600, 1),
        'samples': len(lat), 'dropped_over_cap': state['lat_dropped'],
        'uncontrolled_curve': curve,
        'controlled_by_output': grid,
        'read_this_first': ('未控制的曲线混着任务难度（难任务同时导致上下文长、输出多）。'
                            '引用时必须用 controlled_by_output；若各输出层的放大倍数差异很大，'
                            '说明上下文效应依赖场景，不能给一个笼统倍数。'),
    }

    # 会话集中度
    excess = []
    for sid, c in state['sessions'].items():
        if len(c) < 2:
            continue
        b = min([x for x in c if x > 0], default=0)
        excess.append((sum(c) - b * len(c), sid, len(c), round(st.mean(c))))
    excess.sort(reverse=True)
    tot_ex = sum(e[0] for e in excess) or 1
    f['sessions_concentration'] = {
        'top10_pct_of_behavioral': round(sum(e[0] for e in excess[:10]) / tot_ex * 100, 1),
        'top10': [{'turns': t, 'avg_ctx': a, 'excess_tokens': int(x)} for x, _, t, a in excess[:10]],
    }

    # 项目：含增长模式判定（拖太长型 vs 每轮载重型）
    projs = []
    for p, r in state['projects'].items():
        if r['turns'] < 50:
            continue
        xs = [i for i, _ in r['seq']]
        ys = [c for _, c in r['seq']]
        sl = slope(xs, ys)
        co = pearson(xs, ys)
        avg = st.mean(r['ctx'])
        base = min([x for x in r['ctx'] if x > 0], default=0)
        beh = (1 - base / avg) * 100 if avg else 0
        kind = None
        if sl is not None and co is not None:
            if co >= 0.5 and sl >= 200:
                kind = '拖太长型'          # 上下文随轮次稳定增长 → 换气有效
            elif avg >= (pct(ctxs, .5) or 0) and (co < 0.3 or (sl or 0) < 100):
                kind = '每轮载重型'        # 上下文高但不增长 → 换气无效，要减少单轮读入
        projs.append({
            'name': p, 'turns': r['turns'], 'sessions': len(r['sessions']),
            'cost_pct': round(r['cost'] / total_cost * 100, 1),
            'avg_ctx': round(avg), 'p90_ctx': pct(r['ctx'], .9),
            'behavioral_pct': round(beh, 1),
            'ctx_slope_per_turn': sl, 'ctx_turn_corr': co, 'growth_type': kind,
        })
    projs.sort(key=lambda x: -x['cost_pct'])
    f['projects'] = projs
    f['projects_note'] = ('growth_type 决定给什么建议：拖太长型→换气；每轮载重型→减少单轮读入量。'
                          '两者混为一谈会给出无效建议。')

    # compact
    f['compact'] = {
        'total': sum(state['compact'].values()),
        'auto': state['compact']['auto'], 'manual': state['compact']['manual'],
        'trigger_source': 'compact_boundary 的 compactMetadata.trigger（权威字段，已跨文件去重）',
        'pre_tokens_median': {k: pct(v, .5) for k, v in state['compact_pre'].items() if v},
        'before_median': pct(state['compact_before'], .5),
        'before_min': min(state['compact_before']) if state['compact_before'] else None,
        'before_max': max(state['compact_before']) if state['compact_before'] else None,
        'after_median': pct(state['compact_after'], .5),
        'caveat': 'before_* 是观测到的分布，不是系统阈值——不同模型窗口不同，且该值系统性偏低。',
    }

    # 工具失败
    tc = sum(state['tool_calls'].values())
    te = sum(state['tool_err'].values())
    f['tools'] = {
        'calls': tc, 'errors': te,
        'error_rate_pct': round(te / tc * 100, 2) if tc else None,
        'by_tool': [{'name': n, 'calls': c, 'errors': state['tool_err'].get(n, 0),
                     'error_rate_pct': round(state['tool_err'].get(n, 0) / c * 100, 1)}
                    for n, c in state['tool_calls'].most_common(15)],
    }

    # 提示质量（仅人类会话）
    # ⚠ 程序化调用必须剔除：应用/定时任务会用固定人设提示词反复开会话，
    #   它们不是人在打字。若不剔除，样本会被稀释（某次实测：586 个会话里只有 103 个是人）。
    #   检测方式不硬编码任何应用名——凡"开场白高度雷同并在多个会话中重复"的，判为模板。
    sig_count = Counter()
    for v in state['human'].values():
        if v['msgs']:
            sig_count[v['first_sig']] += 1
    template_sigs = {s for s, n in sig_count.items() if n >= 5}
    human_v = [v for v in state['human'].values()
               if v['msgs'] and v['first_sig'] not in template_sigs]
    f_prog = sum(sig_count[s] for s in template_sigs)
    firsts = [v['msgs'][0] for v in human_v]
    allc = [n for s in state['edits'].values() for n in s.values()]
    heavy = [n for n in allc if n >= 8]
    f['prompt_quality'] = {
        'human_sessions': len(firsts),
        'programmatic_sessions_excluded': f_prog,
        'exclusion_rule': '开场白（前200字）在 ≥5 个会话中重复者判为应用/定时任务的模板，已剔除。',
        'first_msg_chars': {'p25': pct(firsts, .25), 'p50': pct(firsts, .5), 'p75': pct(firsts, .75)},
        'short_opener_pct': round(sum(1 for n in firsts if n < 30) / len(firsts) * 100, 1) if firsts else None,
        'correction_rate_pct': round(state['corrections'] / state['user_msgs'] * 100, 1) if state['user_msgs'] else None,
        'rework': {
            'files': len(allc),
            'median_edits': pct(allc, .5),
            'heavy_file_pct': round(len(heavy) / len(allc) * 100, 1) if allc else None,
            'heavy_share_of_edits_pct': round(sum(heavy) / sum(allc) * 100, 1) if allc else None,
        },
        'caveat': ('只有 first_msg_chars 是干净的行为指标（不受任务难度影响）。'
                   'rework 混着"没说清导致返工"与"这活本来就要反复调"，数据分不开；'
                   'correction_rate 是字符串匹配，必然误伤。三者都只能看自身趋势，不能当 KPI。'),
    }

    # 资产沉淀
    git = novcs = missing = temp = 0.0
    for cwd, c in state['cwd_cost'].items():
        if any(m in cwd for m in TEMP_MARKS):
            temp += c
        if not os.path.isdir(cwd):
            missing += c
        else:
            try:
                ok = subprocess.run(['git', '-C', cwd, 'rev-parse', '--git-dir'],
                                    capture_output=True, timeout=5).returncode == 0
            except Exception:
                ok = False
            if ok:
                git += c
            else:
                novcs += c
    f['assets'] = {
        'in_git_pct': round(git / total_cost * 100, 1),
        'no_vcs_pct': round(novcs / total_cost * 100, 1),
        'path_missing_pct': round(missing / total_cost * 100, 1),
        'temp_path_pct': round(temp / total_cost * 100, 1),
        'caveat': 'path_missing 不等于"工作已丢失"——多数是目录被移动/改名。必须逐个核实后才能下结论。',
    }

    f['codex'] = codex
    f['sidechain'] = {
        'turns': state['sidechain']['turns'],
        'avg_ctx': round(st.mean(state['sidechain']['ctx'])) if state['sidechain']['ctx'] else None,
        'warning': ('子 agent 轮次已从所有主指标中排除。把它们混进平均数会产生辛普森悖论：'
                    '大量小上下文轮次会把主对话的真实负担稀释掉，得出"很省"的假结论。'),
    }
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-o', '--out', default='facts.json')
    args = ap.parse_args()

    state = {
        'scan': {'claude_files': 0, 'read_errors': 0},
        'tok': {'input': 0, 'cache_write': 0, 'cache_read': 0, 'output': 0},
        'turns': 0, 'ctx_all': [], 'by_month': defaultdict(list),
        'sessions': defaultdict(list), 'sess_cwd': {}, 'sess_model': defaultdict(set),
        'projects': defaultdict(lambda: {'turns': 0, 'ctx': [], 'cost': 0.0,
                                         'sessions': set(), 'seq': []}),
        'cwd_cost': defaultdict(float),
        'lat': [], 'lat_dropped': 0, 'wait_s': 0.0,
        'tool_calls': Counter(), 'tool_err': Counter(), 'tool_of': {},
        'edits': defaultdict(Counter),
        'human': defaultdict(lambda: {'msgs': [], 'cwd': '', 'first_sig': ''}),
        'corrections': 0, 'user_msgs': 0,
        'compact': Counter(), 'compact_before': [], 'compact_after': [],
        'compact_seen': set(), 'compact_pre': {'auto': [], 'manual': []},
        'sidechain': {'turns': 0, 'ctx': []},
    }

    if not glob.glob(os.path.expanduser('~/.claude/projects/*')):
        print('未找到 ~/.claude/projects —— 没有 Claude Code 日志可扫。', file=sys.stderr)
        sys.exit(2)

    scan_claude(state)
    codex = scan_codex(state)
    facts = build_facts(state, codex)

    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump(facts, fh, ensure_ascii=False, indent=2)

    s = facts['scan']
    print(f"已写入 {args.out}")
    print(f"  窗口       {SINCE} ~ {UNTIL}")
    print(f"  主对话轮次 {s['main_turns']:,}   会话 {s['sessions']:,}   "
          f"（另有子 agent {s['sidechain_turns']:,} 轮，已排除）")
    pq = facts['prompt_quality']
    print(f"  真人会话   {pq['human_sessions']:,}"
          f"（另剔除 {pq['programmatic_sessions_excluded']:,} 个应用/定时任务的程序化会话）")
    print(f"  结构性下限 {facts['floor']['structural_pct']}%   "
          f"行为性 {facts['floor']['behavioral_pct']}%（可压缩量上界）")
    print(f"  等待总时长 {facts['latency']['total_wait_hours']} 小时")
    if codex:
        print(f"  Codex      {codex['sessions']:,} 会话（已检出）")
    else:
        print("  Codex      未检出，跨工具章节将不出现")


if __name__ == '__main__':
    main()
