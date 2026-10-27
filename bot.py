import json, urllib.request, urllib.parse, datetime, os, time
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (crypto-content-bot)"}
MAIN = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}
SKIP = {"usdt", "usdc", "dai", "usde", "fdusd", "tusd", "usds", "pyusd",
        "wbtc", "steth", "wsteth", "weth", "weeth", "cbbtc", "usdd", "busd"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=20).read()


# --- Prices and movers (required) ---
markets = json.loads(get(
    "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
    "&order=market_cap_desc&per_page=100&page=1&price_change_percentage=24h"))
by_id = {c["id"]: c for c in markets}

price_lines = []
for cid, sym in MAIN.items():
    c = by_id[cid]
    chg = c["price_change_percentage_24h"] or 0
    arrow = "🟢" if chg >= 0 else "🔴"
    price_lines.append(f"{arrow} {sym}: ${c['current_price']:,.2f} ({chg:+.2f}%)")

movers = [c for c in markets
          if c["symbol"].lower() not in SKIP
          and c.get("price_change_percentage_24h") is not None
          and (c.get("market_cap") or 0) >= 1_000_000_000
          and (c.get("total_volume") or 0) >= 50_000_000]
if len(movers) < 2:  # fallback so the post never breaks
    movers = [c for c in markets
              if c["symbol"].lower() not in SKIP
              and c.get("price_change_percentage_24h") is not None]
gainer = max(movers, key=lambda c: c["price_change_percentage_24h"])
loser = min(movers, key=lambda c: c["price_change_percentage_24h"])
gain_line = (f"📈 Top gainer (top 100): {gainer['symbol'].upper()} "
             f"{gainer['price_change_percentage_24h']:+.1f}%")
lose_line = (f"📉 Top loser (top 100): {loser['symbol'].upper()} "
             f"{loser['price_change_percentage_24h']:+.1f}%")

# --- Fear & Greed (optional) ---
fg_line = None
try:
    fg = json.loads(get("https://api.alternative.me/fng/"))["data"][0]
    fg_line = f"😶 Fear & Greed: {fg['value']} ({fg['value_classification']})"
except Exception as e:
    print("Fear & Greed failed:", e)

# --- Headline (optional) ---
headline = None
try:
    root = ET.fromstring(get("https://www.coindesk.com/arc/outboundfeeds/rss/"))
    item = root.find("./channel/item")
    headline = (item.findtext("title").strip(), item.findtext("link").strip())
except Exception as e:
    print("Headline failed:", e)

# --- 7-day chart (optional) ---
chart_url = None
try:
    datasets, labels = [], []
    for cid, sym in MAIN.items():
        time.sleep(3)  # be gentle with the free API
        raw = json.loads(get(
            f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart"
            "?vs_currency=usd&days=7&interval=daily"))["prices"]
        base = raw[0][1]
        datasets.append({"label": sym, "fill": False,
                         "data": [round((p[1] / base - 1) * 100, 2) for p in raw]})
        if not labels:
            labels = [datetime.datetime.utcfromtimestamp(p[0] / 1000).strftime("%d %b")
                      for p in raw]
    cfg = {"type": "line",
           "data": {"labels": labels, "datasets": datasets},
           "options": {"title": {"display": True,
                                 "text": "7-day performance (% change)"}}}
    chart_url = ("https://quickchart.io/chart?w=800&h=450&bkg=white&c="
                 + urllib.parse.quote(json.dumps(cfg, separators=(",", ":"))))
except Exception as e:
    print("Chart failed:", e)

today = datetime.date.today().isoformat()

# --- Build posts ---
x_parts = [f"Crypto check {today}", ""] + price_lines
if fg_line:
    x_parts.append(fg_line)
x_parts += [gain_line, "", "Not financial advice. #crypto #bitcoin"]
x_post = "\n".join(x_parts)
if len(x_post) > 280:
    x_parts.remove(gain_line)
    x_post = "\n".join(x_parts)

tg_parts = [f"Crypto snapshot {today}", ""] + price_lines + [""]
if fg_line:
    tg_parts.append(fg_line)
tg_parts += [gain_line, lose_line]
if headline:
    tg_parts += ["", f"Top story: {headline[0]}", headline[1]]
tg_parts += ["", "Not financial advice. #crypto #bitcoin"]
tg_post = "\n".join(tg_parts)

# --- Save draft ---
os.makedirs("drafts", exist_ok=True)
with open(f"drafts/{today}.txt", "w", encoding="utf-8") as f:
    f.write("=== X POST ===\n" + x_post
            + "\n\n=== CHART IMAGE (open link, save image, attach to X) ===\n"
            + (chart_url or "none")
            + "\n\n=== TELEGRAM POST ===\n" + tg_post)
print(tg_post)
print(f"\n[X post length: {len(x_post)}]")


# --- Telegram ---
def tg(method, fields):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(fields).encode())
    urllib.request.urlopen(req, timeout=30)


token = os.environ.get("TG_TOKEN")
chat = os.environ.get("TG_CHAT")
if token and chat:
    sent = False
    if chart_url and len(tg_post) <= 1024:
        try:
            tg("sendPhoto", {"chat_id": chat, "photo": chart_url, "caption": tg_post})
            sent = True
            print("Sent to Telegram with chart")
        except Exception as e:
            print("Photo send failed:", e)
    if not sent:
        try:
            tg("sendMessage", {"chat_id": chat, "text": tg_post})
            print("Sent to Telegram (text only)")
        except Exception as e:
            print("Telegram failed:", e)
else:
    print("Telegram secrets not set, skipping")
