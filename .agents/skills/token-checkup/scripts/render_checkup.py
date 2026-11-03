#!/usr/bin/env python3
"""render_checkup.py — facts.json + history.jsonl → 一页纸趋势对比。

日常体检用这个，不是全量报告。它只回答一个问题：**跟上次比，我变了没有。**
刻意不重述上次的结论——那份报告还在，翻回去看就行。
"""
import argparse, html, json, os, sys
from theme import page, k, delta

ESC = html.escape

# (字段, 显示名, 单位, 越低越好, 格式化函数)
METRICS = [
    ('ctx_p50',                 '每轮上下文（中位）',  '', True,  lambda v: k(v)),
    ('ctx_p90',                 '每轮上下文（P90）',   '', True,  lambda v: k(v)),
    ('behavioral_pct',          '重读中的行为性占比',  '%', True, lambda v: f'{v:.0f}%'),
    ('top10_pct_of_behavioral', '最长 10 会话的占比',  '%', True, lambda v: f'{v:.0f}%'),
    ('wait_hours',              '等待总时长',          'h', True, lambda v: f'{v:.0f}h'),
    ('compact_manual',          '主动压缩次数',        '',  False, lambda v: f'{v:,}'),
    ('first_msg_p50',           '开场消息长度（中位）', '字', False, lambda v: f'{v}字'),
    ('short_opener_pct',        '少于30字开场的比例',  '%', True, lambda v: f'{v:.0f}%'),
    ('rework_heavy_pct',        '被改8次以上的文件',   '%', True, lambda v: f'{v:.0f}%'),
    ('correction_rate_pct',     '含纠正语的消息',      '%', True, lambda v: f'{v:.0f}%'),
    ('cache_hit_pct',           '缓存命中率',          '%', False, lambda v: f'{v:.0f}%'),
    ('tool_error_pct',          '工具失败率',          '%', True, lambda v: f'{v:.2f}%'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('facts', nargs='?', default='facts.json')
    ap.add_argument('history', nargs='?', default='history.jsonl')
    ap.add_argument('-o', '--out', default='Token体检_趋势.html')
    args = ap.parse_args()

    f = json.load(open(args.facts, encoding='utf-8'))
    if not os.path.exists(args.history):
        print('没有 history.jsonl —— 这是第一次体检，请改用 render_report.py 出全量版。',
              file=sys.stderr)
        sys.exit(2)

    rows = [json.loads(l) for l in open(args.history, encoding='utf-8') if l.strip()]
    if len(rows) < 2:
        print(f'history.jsonl 只有 {len(rows)} 条记录，无法做趋势对比。'
              '请先用 render_report.py 出全量版，下次再来。', file=sys.stderr)
        sys.exit(2)

    cur, prev = rows[-1], rows[-2]
    first = rows[0]

    trs = ''
    regress = []
    for key, label, unit, lower_better, fmt in METRICS:
        now, was = cur.get(key), prev.get(key)
        if now is None:
            continue
        txt, cls = delta(now, was, unit, lower_better)
        if cls == 'up':
            regress.append(label)
        base = f' <span style="color:var(--ink3)">（首次 {fmt(first[key])}）</span>' \
            if first.get(key) is not None and len(rows) > 2 else ''
        trs += (f'<tr><td>{ESC(label)}</td>'
                f'<td class="num">{fmt(was) if was is not None else "—"}</td>'
                f'<td class="num">{fmt(now)}{base}</td>'
                f'<td class="num"><span class="delta {cls}">{txt}</span></td></tr>')

    warn = ''
    if regress:
        warn = ('<div class="caveat"><h3>⚠ 这几项退步了</h3><ul>'
                + ''.join(f'<li>{ESC(x)}</li>' for x in regress)
                + '</ul><p style="font-size:14px;color:var(--ink2);margin:8px 0 0">'
                  '退步不一定是习惯变差——换了项目、接了更难的活，都会让这些数字上升。'
                  '看到退步先问"我这段时间在做什么"，再判断。</p></div>')

    span = f"{ESC(prev['generated_at'][:10])} → {ESC(cur['generated_at'][:10])}"
    body = f'''
  <div class="eyebrow">Token 体检 · 趋势对比</div>
  <h1>跟上次比，<br>你变了没有</h1>
  <p class="dek">{span}　·　第 {len(rows)} 次体检</p>

  <div class="tblwrap"><table>
    <thead><tr><th>指标</th><th class="num">上次</th><th class="num">这次</th>
    <th class="num">变化</th></tr></thead>
    <tbody>{trs}</tbody>
  </table></div>

  {warn}

  <div class="note">
    <b>怎么读这张表：</b>绿色是往好的方向走，红色是反向。
    但<b>单次变化不足以说明习惯改变</b>——两个点画不出趋势，
    至少要 3 次以上，而且要排除"这段时间在做完全不同的项目"这个混淆。
  </div>

  <div class="note">
    <b>本次规模：</b>{f['scan']['main_turns']:,} 轮主对话 / {f['scan']['sessions']:,} 会话
    · 真人会话 {f['prompt_quality']['human_sessions']:,}
    （已剔除 {f['prompt_quality']['programmatic_sessions_excluded']:,} 个程序化会话）<br>
    想看完整分析：<code>python3 scripts/render_report.py facts.json</code>
  </div>

  <hr>
  <div class="foot">
    由 <code>token-checkup</code> 生成 · 全部数据来自本机日志，未上传任何内容<br>
    历史记录 {len(rows)} 条，存于 <code>{ESC(args.history)}</code>
  </div>
'''
    open(args.out, 'w', encoding='utf-8').write(page('Token 体检 · 趋势', body))
    print(f'已生成 {args.out}（第 {len(rows)} 次体检，对比 {span}）')
    if regress:
        print(f'⚠ 退步项：{"、".join(regress)}')


if __name__ == '__main__':
    main()
