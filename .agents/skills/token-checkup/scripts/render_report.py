#!/usr/bin/env python3
"""render_report.py — facts.json → 全量体检报告 HTML。

⚠ 本文件只渲染**测量结果**，不产出叙事结论。
   它刻意不写"你的坏习惯是 X""你浪费了 Y"这类判断——那是 Claude 读完 facts.json，
   在 narrative-rules.md 的约束下现场写的。模板写死判断 = 把一次性的错误固化成每次都犯。

模板负责的是：把数字摆对、把口径和局限标清楚、把不该比的东西不放在一起比。
"""
import argparse, html, json, sys
from theme import page, k, bar, CSS  # noqa: F401

ESC = html.escape


def sec_header(f):
    m, s = f['meta'], f['scan']
    w = m['window']
    win = ('全部历史' if w['since'] == '0000-00-00' and w['until'] == '9999-99-99'
           else f"{w['since']} ~ {w['until']}")
    lat = f['latency']
    return f'''
  <div class="eyebrow">Token 体检 · 全量报告</div>
  <h1>你的 token 花在哪，<br>你的时间等在哪</h1>
  <p class="dek">这份报告只陈述从你自己日志里测出来的数字。
  它不下"健康 / 浪费"之类的判断——没有权威标准可依，所有的线都该由你自己定。</p>
  <div class="byline">
  数据源：<code>~/.claude/projects</code>{'· <code>~/.codex/sessions</code>' if f.get('codex') else ''}
  · 时间窗 {ESC(win)}<br>
  主对话 {s['main_turns']:,} 轮 / {s['sessions']:,} 会话
  · 另有子 agent {s['sidechain_turns']:,} 轮（已排除，理由见文末）<br>
  生成于 {ESC(m['generated_at'])}
  </div>

  <div class="hero">
    <div class="n">{lat['total_wait_hours']:.0f}<small> 小时</small></div>
    <div class="cap">这是你<b>在等模型回话</b>上花掉的时间，共 {lat['samples']:,} 轮，
    折合 <b>{lat['total_wait_hours']/8:.0f} 个工作日</b>。<br>
    已剔除 {lat['dropped_over_cap']:,} 个超过 10 分钟的样本（视为人离开了）。</div>
  </div>

  <div class="plain">
    <div class="t">先说清楚一件事</div>
    <p><b>模型没有记忆。</b>你每问一句，它都要把之前说过的全部内容重读一遍，然后才回答。</p>
    <p>所以第 1 轮它读 1 页，第 200 轮可能在读几百页——<b>就为了回答你一句"嗯，然后呢"。</b></p>
    <p>这意味着<b>重读本身是架构决定的，不是坏习惯</b>。
    真正要问的是：这些重读里，有多少是躲不掉的？下一节给出分母。</p>
  </div>
'''


def sec_floor(f):
    fl = f['floor']
    return f'''
  <h2><span class="num">01</span>重读里，有多少是躲不掉的</h2>
  <p class="lede">假设你每一轮都开新对话、完全不积累历史，那些无论如何都要重读的固定内容有多少？
  这个数就是分母。</p>

  <div class="verdict">
    <h3>重读量的构成</h3>
    <div class="n">{fl['behavioral_pct']:.0f}<small>%</small></div>
    <p>只有 <b>{fl['structural_pct']:.0f}%</b> 是架构决定、砍不掉的。
    剩下 <b>{fl['behavioral_pct']:.0f}%</b> 来自历史累积——<b>这部分才是能改的</b>。</p>
    <p style="margin-top:10px">而且它高度集中：<b>最长的 10 个会话贡献了其中的
    {f['sessions_concentration']['top10_pct_of_behavioral']:.0f}%</b>。</p>
  </div>

  <div class="note"><b>口径：</b>{ESC(fl['method'])}<br>
  <b>⚠ 这不是可省收益：</b>{ESC(fl['caveat'])}</div>
'''


def sec_latency(f):
    lat = f['latency']
    rows = ''
    for r in lat['controlled_by_output']:
        cells = ''.join(
            f'<td class="num">{c["median_s"]:.1f}s</td>' if c['median_s'] else '<td class="num">—</td>'
            for c in r['cells'])
        amp = f'{r["amplification"]:.2f}×' if r['amplification'] else '—'
        cls = ' class="bad"' if r['amplification'] and r['amplification'] >= 2 else (
            ' class="win"' if r['amplification'] and r['amplification'] < 1 else '')
        rows += f'<tr><td>{ESC(r["output_bin"])}</td>{cells}<td class="num"{cls}>{amp}</td></tr>'
    heads = ''.join(f'<th class="num">{ESC(c["ctx_bin"])}</th>'
                    for c in lat['controlled_by_output'][0]['cells'])
    curve = ''
    mx = max((c['median_s'] for c in lat['uncontrolled_curve']), default=1)
    for c in lat['uncontrolled_curve']:
        tone = 'hot' if c['median_s'] >= mx * .8 else ('warm' if c['median_s'] >= mx * .55 else '')
        curve += bar(c['bin'], c['median_s'], mx, f"{c['median_s']:.1f}s", tone)
    return f'''
  <h2><span class="num">02</span>上下文和响应速度</h2>
  <p class="lede">先看未经处理的曲线，再看控制变量之后的版本——两者结论不同，
  <b>能引用的是后者</b>。</p>

  <div class="bars">{curve}</div>
  <p class="note"><b>⚠ 上面这张图不能直接引用。</b>{ESC(lat['read_this_first'])}</p>

  <h3>控制输出长度后</h3>
  <p>同一行内的样本输出长度基本相同，剩下的差异才更可能来自上下文本身。</p>
  <div class="tblwrap"><table>
    <thead><tr><th>回复长度</th>{heads}<th class="num">层内放大</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="note">若各行的放大倍数差异很大，说明<b>上下文的影响依赖场景</b>，
  不能给出一个笼统的"慢 N 倍"。</p>
'''


def sec_context(f):
    c = f['context']
    return f'''
  <h2><span class="num">03</span>你的上下文分布</h2>
  <p class="lede">这一节<b>只给分布，不给判断</b>。目前没有任何权威标准说明多少算健康，
  实测也不存在拐点——只有连续递增的代价。<b>线该由你自己定。</b></p>
  <div class="tblwrap"><table>
    <thead><tr><th>分位</th><th class="num">P25</th><th class="num">P50</th>
    <th class="num">P75</th><th class="num">P90</th><th class="num">P99</th></tr></thead>
    <tbody><tr><td>每轮上下文</td>
      <td class="num">{k(c['p25'])}</td><td class="num">{k(c['p50'])}</td>
      <td class="num">{k(c['p75'])}</td><td class="num">{k(c['p90'])}</td>
      <td class="num">{k(c['p99'])}</td></tr></tbody>
  </table></div>
  <p class="note"><b>怎么用：</b>建议从 P50 往下砍 30% 作为起步线，写进状态栏。
  它是<b>你的操作线，不是行业标准</b>。</p>
'''


def sec_projects(f):
    rows = ''
    for p in f['projects'][:12]:
        gt = p['growth_type'] or '—'
        tone = ' class="bad"' if gt == '拖太长型' else (' class="win"' if gt == '每轮载重型' else '')
        rows += (f'<tr><td>{ESC(p["name"])}</td><td class="num">{p["cost_pct"]:.1f}%</td>'
                 f'<td class="num">{p["turns"]:,}</td><td class="num">{k(p["avg_ctx"])}</td>'
                 f'<td class="num">{k(p["p90_ctx"])}</td>'
                 f'<td{tone}>{ESC(gt)}</td></tr>')
    return f'''
  <h2><span class="num">04</span>按项目：钱花在哪，以及该开什么药方</h2>
  <p class="lede">最后一列决定建议内容。<b>两种类型的药方完全不同，混为一谈会给出无效建议。</b></p>
  <div class="tblwrap"><table>
    <thead><tr><th>项目</th><th class="num">成本占比</th><th class="num">轮次</th>
    <th class="num">均上下文</th><th class="num">P90</th><th>增长类型</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <div class="note">
    <b>拖太长型</b>（上下文随轮次稳定增长）→ 换气有效：开新对话或压缩。<br>
    <b>每轮载重型</b>（上下文高但不随轮次增长）→ <b>换气无效</b>，要减少单轮读入量：
    给精确路径和行段，别把整个目录灌进去。<br>
    <b>—</b> 表示判定证据不足，只看数字，不给建议。
  </div>
'''


def sec_checked(f):
    t, cp, a = f['tools'], f['compact'], f['assets']
    ch = f['cost']['cache_hit_rate_pct']
    return f'''
  <h2><span class="num">05</span>测过并排除的项</h2>
  <p class="lede">这一节和上面同样重要——<b>它是这份报告可信的证明</b>：
  测了这些，都没问题，所以剩下的那个才是真的。</p>
  <div class="tblwrap"><table>
    <thead><tr><th>怀疑项</th><th class="num">实测</th><th>判决</th></tr></thead>
    <tbody>
      <tr><td>缓存反复失效，在重复付全价</td><td class="num">命中率 {ch:.0f}%</td>
        <td class="{'win' if ch >= 90 else 'bad'}">{'✅ 无问题' if ch >= 90 else '⚠ 值得看'}</td></tr>
      <tr><td>工具调用老失败，白烧 token</td><td class="num">失败率 {t['error_rate_pct']:.2f}%</td>
        <td class="{'win' if (t['error_rate_pct'] or 0) < 5 else 'bad'}">
        {'✅ 无问题' if (t['error_rate_pct'] or 0) < 5 else '⚠ 值得看'}</td></tr>
      <tr><td>工作散落临时目录，做完就丢</td><td class="num">临时路径 {a['temp_path_pct']:.1f}%</td>
        <td class="{'win' if a['temp_path_pct'] < 5 else 'bad'}">
        {'✅ 无问题' if a['temp_path_pct'] < 5 else '⚠ 值得看'}</td></tr>
      <tr><td>投入没沉淀成可复用资产</td><td class="num">在 git 内 {a['in_git_pct']:.0f}%</td>
        <td class="{'win' if a['in_git_pct'] >= 60 else 'bad'}">
        {'✅ 大部分已沉淀' if a['in_git_pct'] >= 60 else '⚠ 值得看'}</td></tr>
      <tr><td>压缩（compact）用得太多</td>
        <td class="num">{cp['total']} 次，主动 {cp['manual']} 次</td>
        <td class="{'win' if cp['manual'] == 0 else ''}">
        {'✅ 相反：一次都没主动按过' if cp['manual'] == 0 else '已在主动使用'}</td></tr>
    </tbody>
  </table></div>
  <p class="note"><b>关于 {a['path_missing_pct']:.1f}% 的"原路径已不存在"：</b>
  {ESC(a['caveat'])}</p>
  <p class="note"><b>压缩触发时的上下文：</b>中位 {k(cp['before_median'])}，
  范围 {k(cp['before_min'])} – {k(cp['before_max'])}，压缩后中位 {k(cp['after_median'])}。<br>
  {ESC(cp['caveat'])}</p>
'''


def sec_prompt(f):
    q = f['prompt_quality']
    r = q['rework']
    return f'''
  <h2><span class="num">06</span>你怎么提需求</h2>
  <p class="lede">三个指标里<b>只有第一个是干净的</b>，理由见下。</p>
  <div class="tblwrap"><table>
    <thead><tr><th>指标</th><th class="num">实测</th><th>可信度</th></tr></thead>
    <tbody>
      <tr><td>开场消息长度（中位）</td>
        <td class="num">{q['first_msg_chars']['p50']} 字</td>
        <td class="win">高 — 测的是行为，几乎不受任务难度影响</td></tr>
      <tr><td>以少于 30 字开场的比例</td><td class="num">{q['short_opener_pct']}%</td>
        <td class="win">高 — 同上</td></tr>
      <tr><td>同一文件被改 8 次以上</td><td class="num">{r['heavy_file_pct']}%</td>
        <td>中 — 混着"没说清"与"这活本来就要反复调"</td></tr>
      <tr><td>消息含纠正语</td><td class="num">{q['correction_rate_pct']}%</td>
        <td>低 — 字符串匹配，必然误伤，只能看自身趋势</td></tr>
    </tbody>
  </table></div>
  <p class="note">样本：<b>{q['human_sessions']:,} 个真人会话</b>
  （已剔除 {q['programmatic_sessions_excluded']:,} 个程序化会话——{ESC(q['exclusion_rule'])}）<br>
  那 {r['heavy_file_pct']}% 被反复修改的文件吃掉了 <b>{r['heavy_share_of_edits_pct']}%</b> 的编辑动作。</p>
  <p class="note">{ESC(q['caveat'])}</p>
'''


def sec_codex(f):
    cx = f.get('codex')
    if not cx:
        return ('\n  <h2><span class="num">07</span>跨工具对照</h2>\n'
                '  <p class="lede">未检测到 <code>~/.codex/sessions</code>，本节跳过。'
                '这不是错误——只用一个工具是完全正常的。</p>\n')
    return f'''
  <h2><span class="num">07</span>跨工具对照：Codex</h2>
  <div class="tblwrap"><table>
    <thead><tr><th>指标</th><th class="num">数值</th></tr></thead>
    <tbody>
      <tr><td>会话数</td><td class="num">{cx['sessions']:,}</td></tr>
      <tr><td>轮次</td><td class="num">{cx['turns']:,}</td></tr>
      <tr><td>平均每轮上下文</td><td class="num">{k(cx['avg_ctx'])}</td></tr>
      <tr><td>P90 上下文</td><td class="num">{k(cx['p90_ctx'])}</td></tr>
      <tr><td>reasoning token</td><td class="num">{k(cx['reasoning'])}</td></tr>
    </tbody>
  </table></div>
  <p class="note"><b>口径：</b>{ESC(cx['field_source'] or '—')}<br>{ESC(cx['note'])}</p>
'''


def sec_caveats(f):
    return f'''
  <div class="caveat">
    <h3>这份报告不能证明什么</h3>
    <ul>
      <li><b>"{f['floor']['behavioral_pct']:.0f}% 是行为造成的"是上界，不是可省收益。</b>
      真开新对话要重新交代背景、重读文件，实际能省的更少。这是会计恒等式，不是因果估计。</li>
      <li><b>没有行业基准。</b>本报告不做横向对比——所有判断都是你和你自己比。
      任何声称"业界标准是 X"的说法都应被怀疑。</li>
      <li><b>时间成本含混淆。</b>难任务同时导致上下文长和输出多。已按输出长度分层来缓解，
      但无法完全分离。</li>
      <li><b>月度对比不足以判断进步。</b>期间换过项目就会混淆，需至少 3 次体检才谈得上趋势。</li>
      <li><b>子 agent 轮次已全部排除。</b>{ESC(f['sidechain']['warning'])}</li>
      <li><b>成本是相对权重，不是账单。</b>{ESC(f['meta']['weights_note'])}</li>
    </ul>
  </div>
  <hr>
  <div class="foot">
    由 <code>token-checkup</code> 生成。全部数据来自本机日志，未上传任何内容。<br>
    每个数字都可指回 <code>facts.json</code>；叙事受 <code>reference/narrative-rules.md</code> 约束。<br>
    子 agent 轮次：{f['scan']['sidechain_turns']:,}（已排除）
    · 读取失败文件数：{f['scan'].get('read_errors', 0)}
  </div>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('facts', nargs='?', default='facts.json')
    ap.add_argument('-o', '--out', default='Token体检报告.html')
    args = ap.parse_args()

    f = json.load(open(args.facts, encoding='utf-8'))
    if f.get('schema_version') != 2:
        print(f'⚠ facts.json 的 schema_version 是 {f.get("schema_version")}，'
              f'本渲染器预期 2。请重新运行 scan.py。', file=sys.stderr)
        sys.exit(1)

    body = ''.join([sec_header(f), sec_floor(f), sec_latency(f), sec_context(f),
                    sec_projects(f), sec_checked(f), sec_prompt(f), sec_codex(f),
                    sec_caveats(f)])
    open(args.out, 'w', encoding='utf-8').write(page('Token 体检报告', body))
    print(f'已生成 {args.out}')
    print('⚠ 模板只摆数字，不写结论。请按 narrative-rules.md 补写叙事后再交付。')


if __name__ == '__main__':
    main()
