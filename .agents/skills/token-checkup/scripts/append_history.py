#!/usr/bin/env python3
"""append_history.py — 把本次体检的关键指标追加进 history.jsonl，供下次做趋势对比。

只存**可跨次比较**的标量。刻意不存：
  · 项目排行（项目会变，无法对齐）
  · 任何判断性结论（判断由 narrative-rules 约束，不该固化进数据）
"""
import argparse, json, os, sys

FIELDS = [
    ('window_until',        lambda f: f['meta']['window']['until']),
    ('main_turns',          lambda f: f['scan']['main_turns']),
    ('sessions',            lambda f: f['scan']['sessions']),
    ('human_sessions',      lambda f: f['prompt_quality']['human_sessions']),
    ('ctx_p50',             lambda f: f['context']['p50']),
    ('ctx_p90',             lambda f: f['context']['p90']),
    ('ctx_mean',            lambda f: f['context']['mean']),
    ('structural_pct',      lambda f: f['floor']['structural_pct']),
    ('behavioral_pct',      lambda f: f['floor']['behavioral_pct']),
    ('top10_pct_of_behavioral', lambda f: f['sessions_concentration']['top10_pct_of_behavioral']),
    ('wait_hours',          lambda f: f['latency']['total_wait_hours']),
    ('cache_hit_pct',       lambda f: f['cost']['cache_hit_rate_pct']),
    ('tool_error_pct',      lambda f: f['tools']['error_rate_pct']),
    ('compact_total',       lambda f: f['compact']['total']),
    ('compact_manual',      lambda f: f['compact']['manual']),
    ('first_msg_p50',       lambda f: f['prompt_quality']['first_msg_chars']['p50']),
    ('short_opener_pct',    lambda f: f['prompt_quality']['short_opener_pct']),
    ('rework_heavy_pct',    lambda f: f['prompt_quality']['rework']['heavy_file_pct']),
    ('correction_rate_pct', lambda f: f['prompt_quality']['correction_rate_pct']),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('facts', nargs='?', default='facts.json')
    ap.add_argument('-o', '--out', default='history.jsonl')
    args = ap.parse_args()

    facts = json.load(open(args.facts, encoding='utf-8'))
    row = {'generated_at': facts['meta']['generated_at']}
    for name, fn in FIELDS:
        try:
            row[name] = fn(facts)
        except Exception:
            row[name] = None

    # 同一天重复跑不重复追加，改为覆盖当天最后一条
    rows = []
    if os.path.exists(args.out):
        for line in open(args.out, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get('generated_at', '')[:10] != row['generated_at'][:10]:
                rows.append(r)
    rows.append(row)

    with open(args.out, 'w', encoding='utf-8') as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f'已追加基线 → {args.out}（共 {len(rows)} 次记录）')
    if len(rows) == 1:
        print('这是第一次。趋势对比需要至少 2 次；要看出真正的变化，建议 3 次以上。')


if __name__ == '__main__':
    main()
