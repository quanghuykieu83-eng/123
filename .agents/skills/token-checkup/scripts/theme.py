"""theme.py — 两个渲染器共用的样式与小工具。改这里，两份报告一起变。"""

CSS = """
:root{
  --bg:#FBF9F6; --card:#FFF; --line:#E7E1D9;
  --ink:#1F1B17; --ink2:#5C554E; --ink3:#8F8880;
  --red:#A33A2A; --redbg:#FBF0EC; --green:#3F6B4A; --greenbg:#EFF5F0;
  --gold:#8A5A23; --goldbg:#FBF4E8; --blue:#2E5A78; --bluebg:#EDF3F7;
  --dim:#D9D2C8;
  --shadow:0 1px 2px rgba(31,27,23,.05), 0 12px 32px rgba(31,27,23,.05);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#16140F; --card:#1F1C17; --line:#33302A;
    --ink:#F2EDE5; --ink2:#B8B0A5; --ink3:#857D72;
    --red:#E58C7A; --redbg:#2E1F1A; --green:#8FB08F; --greenbg:#1C2620;
    --gold:#DDA267; --goldbg:#2A2318; --blue:#8FB4CE; --bluebg:#1A242B;
    --dim:#3D392F; --shadow:none;
  }
}
:root[data-theme="dark"]{
  --bg:#16140F; --card:#1F1C17; --line:#33302A;
  --ink:#F2EDE5; --ink2:#B8B0A5; --ink3:#857D72;
  --red:#E58C7A; --redbg:#2E1F1A; --green:#8FB08F; --greenbg:#1C2620;
  --gold:#DDA267; --goldbg:#2A2318; --blue:#8FB4CE; --bluebg:#1A242B;
  --dim:#3D392F; --shadow:none;
}
:root[data-theme="light"]{
  --bg:#FBF9F6; --card:#FFF; --line:#E7E1D9;
  --ink:#1F1B17; --ink2:#5C554E; --ink3:#8F8880;
  --red:#A33A2A; --redbg:#FBF0EC; --green:#3F6B4A; --greenbg:#EFF5F0;
  --gold:#8A5A23; --goldbg:#FBF4E8; --blue:#2E5A78; --bluebg:#EDF3F7;
  --dim:#D9D2C8;
  --shadow:0 1px 2px rgba(31,27,23,.05), 0 12px 32px rgba(31,27,23,.05);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;
  font-size:16px;line-height:1.75;-webkit-font-smoothing:antialiased}
.wrap{max-width:820px;margin:0 auto;padding:60px 28px 110px}
.eyebrow{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:12px;
  letter-spacing:.16em;color:var(--ink3);text-transform:uppercase;margin-bottom:16px}
h1{font-family:"Songti SC",Georgia,serif;font-size:42px;line-height:1.22;
  margin:0 0 14px;letter-spacing:-.015em;text-wrap:balance}
h2{font-family:"Songti SC",Georgia,serif;font-size:27px;margin:58px 0 6px;
  letter-spacing:-.01em;line-height:1.3;text-wrap:balance}
h2 .num{color:var(--ink3);font-family:ui-monospace,Menlo,monospace;font-size:13px;
  letter-spacing:.1em;display:block;margin-bottom:9px;font-weight:400}
h3{font-family:"Songti SC",Georgia,serif;font-size:19px;margin:0 0 9px}
p{margin:0 0 16px}
.dek{font-size:17px;color:var(--ink2);margin:0 0 10px;line-height:1.7;max-width:62ch}
.lede{font-size:16px;color:var(--ink2);margin-bottom:26px;max-width:64ch}
.byline{font-size:12.5px;color:var(--ink3);font-family:ui-monospace,Menlo,monospace;
  padding-top:16px;margin-top:20px;border-top:1px solid var(--line);line-height:1.8}
b,strong{font-weight:600}
code{font-family:ui-monospace,Menlo,monospace;font-size:.88em;
  background:var(--goldbg);padding:1px 6px;border-radius:4px;color:var(--gold)}
.hero{margin:44px 0;padding:34px 36px;background:var(--card);border-radius:14px;
  box-shadow:var(--shadow);border-left:4px solid var(--red)}
.hero .n{font-family:"Songti SC",Georgia,serif;font-size:70px;line-height:1;
  letter-spacing:-.03em;color:var(--red)}
.hero .n small{font-size:28px;letter-spacing:0}
.hero .cap{font-size:14.5px;color:var(--ink2);margin-top:12px;line-height:1.7;max-width:56ch}
.hero .cap b{color:var(--ink)}
table{width:100%;border-collapse:collapse;margin:20px 0;font-size:14.5px}
th,td{padding:12px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:11.5px;letter-spacing:.06em;color:var(--ink3);text-transform:uppercase;font-weight:600}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.total td{border-top:2px solid var(--ink);border-bottom:none;font-weight:600;font-size:15.5px}
.win{color:var(--green);font-weight:600}
.bad{color:var(--red);font-weight:600}
.tblwrap{overflow-x:auto}
.bars{margin:20px 0}
.bar{display:flex;align-items:center;gap:13px;margin-bottom:8px;font-size:14px}
.bar .lbl{width:96px;text-align:right;color:var(--ink2);
  font-family:ui-monospace,Menlo,monospace;font-size:12.5px;flex-shrink:0}
.bar .track{flex:1;height:25px;background:var(--dim);border-radius:5px;overflow:hidden;min-width:60px}
.bar .fill{height:100%;background:var(--green);border-radius:5px}
.bar.warm .fill{background:var(--gold)}
.bar.hot .fill{background:var(--red)}
.bar .val{width:96px;color:var(--ink2);font-family:ui-monospace,Menlo,monospace;
  font-size:12.5px;flex-shrink:0}
.note{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:16px 20px;font-size:14px;color:var(--ink2);margin:14px 0}
.note b{color:var(--ink)}
.plain{background:var(--bluebg);border-left:3px solid var(--blue);border-radius:10px;
  padding:22px 26px;margin:24px 0}
.plain .t{font-family:ui-monospace,Menlo,monospace;font-size:11px;letter-spacing:.12em;
  color:var(--blue);text-transform:uppercase;margin-bottom:11px}
.plain p{font-size:15px;color:var(--ink2);margin:0 0 11px}
.plain p:last-child{margin-bottom:0}
.plain b{color:var(--ink)}
.caveat{background:var(--goldbg);border:1px solid var(--gold);border-radius:12px;
  padding:24px 28px;margin:32px 0}
.caveat h3{color:var(--gold);font-size:18px;margin-bottom:11px}
.caveat ul{margin:0;padding-left:20px}
.caveat li{font-size:14px;color:var(--ink2);margin-bottom:9px}
.caveat b{color:var(--ink)}
.verdict{background:var(--greenbg);border:1px solid var(--green);border-radius:14px;
  padding:30px 34px;margin:30px 0}
.verdict h3{color:var(--green);margin-bottom:12px;font-size:21px}
.verdict .n{font-family:"Songti SC",Georgia,serif;font-size:52px;line-height:1;
  color:var(--green);letter-spacing:-.02em}
.verdict .n small{font-size:21px}
.verdict p{font-size:14.5px;color:var(--ink2);margin:14px 0 0}
.delta{font-family:ui-monospace,Menlo,monospace;font-weight:600}
.delta.up{color:var(--red)} .delta.down{color:var(--green)} .delta.flat{color:var(--ink3)}
hr{border:0;border-top:1px solid var(--line);margin:50px 0}
.foot{font-size:12.5px;color:var(--ink3);line-height:1.8;font-family:ui-monospace,Menlo,monospace}
@media(max-width:600px){
  h1{font-size:31px} h2{font-size:23px} .hero{padding:26px 22px} .hero .n{font-size:52px}
  .wrap{padding:40px 18px 80px}
  .bar .lbl{width:70px;font-size:11px} .bar .val{width:74px;font-size:11px}
}
"""


def page(title, body):
    return (f'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title>\n<style>{CSS}</style>\n</head>\n<body>\n'
            f'<div class="wrap">\n{body}\n</div>\n</body>\n</html>\n')


def k(n):
    """token 数 → 人类可读的 K/M。"""
    if n is None:
        return '—'
    if n >= 1_000_000:
        return f'{n/1_000_000:.2f}M'
    if n >= 1000:
        return f'{n/1000:.0f}K'
    return str(int(n))


def bar(label, value, maxv, text, tone=''):
    w = 0 if not maxv else max(2, min(100, value / maxv * 100))
    cls = f'bar {tone}'.strip()
    return (f'<div class="{cls}"><span class="lbl">{label}</span>'
            f'<span class="track"><span class="fill" style="width:{w:.0f}%"></span></span>'
            f'<span class="val">{text}</span></div>')


def delta(now, before, unit='', lower_is_better=True):
    """返回 (箭头文本, css 类)。"""
    if now is None or before is None:
        return ('—', 'flat')
    d = now - before
    if before:
        p = d / before * 100
        txt = f'{"↑" if d > 0 else "↓" if d < 0 else "→"}{abs(p):.0f}%'
    else:
        txt = f'{"↑" if d > 0 else "↓" if d < 0 else "→"}{abs(d):.0f}{unit}'
    if abs(d) < 1e-9:
        return ('→ 持平', 'flat')
    good = (d < 0) if lower_is_better else (d > 0)
    return (txt, 'down' if good else 'up')
