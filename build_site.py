import os, re, glob, html

TG = os.environ.get("TG_CHAT", "")
TG_URL = f"https://t.me/{TG.lstrip('@')}" if TG.startswith("@") else ""
SITE = "Crypto Daily Brief"

CSS = """body{font-family:system-ui,sans-serif;max-width:680px;margin:0 auto;padding:20px;
background:#0b0f19;color:#e6e9f0;line-height:1.6}a{color:#6ea8ff}
h1,h2{line-height:1.2}.card{background:#141a2b;border-radius:10px;padding:16px;margin:16px 0}
img{max-width:100%;border-radius:8px;background:#fff}.small{color:#8b93a7;font-size:.85em}
pre{white-space:pre-wrap;font-family:inherit;margin:0}"""


def page(title, body):
    nav = f'<p><a href="index.html">{SITE}</a>'
    if TG_URL:
        nav += f' · <a href="{TG_URL}">Join on Telegram</a>'
    nav += "</p>"
    foot = ('<p class="small">Educational content only. Not financial advice. '
            'Crypto is volatile and you can lose money. Do your own research.</p>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><style>{CSS}</style></head>'
            f'<body>{nav}{body}{foot}</body></html>')


def linkify(text):
    text = html.escape(text)
    return re.sub(r"(https?://[^\s]+)", r'<a href="\1" rel="nofollow">\1</a>', text)


def sections(raw):
    out = {}
    for name, body in re.findall(r"=== (.*?) ===\n(.*?)(?=\n\n=== |\Z)", raw, re.S):
        out[name.split()[0]] = body.strip()
    return out


os.makedirs("docs", exist_ok=True)
files = sorted(glob.glob("drafts/20??-??-??.txt"), reverse=True)
days = []
for path in files:
    date = os.path.basename(path)[:-4]
    sec = sections(open(path, encoding="utf-8").read())
    tg = sec.get("TELEGRAM")
    if not tg:
        continue
    chart = sec.get("CHART", "")
    body = f"<h1>Crypto snapshot, {date}</h1>"
    if chart.startswith("http"):
        body += f'<img src="{html.escape(chart)}" alt="7-day performance chart">'
    body += f'<div class="card"><pre>{linkify(tg)}</pre></div>'
    with open(f"docs/{date}.html", "w", encoding="utf-8") as f:
        f.write(page(f"Crypto snapshot {date} | {SITE}", body))
    days.append(date)

items = "".join(f'<li><a href="{d}.html">Crypto snapshot, {d}</a></li>' for d in days[:60])
home = (f"<h1>{SITE}</h1><p>A calm daily look at BTC, ETH and SOL, the market mood "
        f"and one headline. No hype, no signals.</p><h2>Latest snapshots</h2><ul>{items}</ul>")
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(page(SITE, home))
print(f"Built {len(days)} day pages")
