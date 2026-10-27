import os, json, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 crypto-content-bot"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def get_json(url):
    return json.loads(get(url))

def arrow(x):
    return "🟢" if x >= 0 else "🔴"

def fmt_price(p):
    return f"${p:,.0f}" if p >= 100 else f"${p:,.2f}"

# --- Market data (top 100 coins) ---
coins = get(
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
    "&price_change_percentage=24h"
)
coins = json.loads(coins)
by_id = {c["id"]: c for c in coins}

lines = []
for cid, sym in [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL")]:
    c = by_id.get(cid)
    if c:
        ch = c["price_change_percentage_24h"] or 0
        lines.append(f"{arrow(ch)} {sym}: {fmt_price(c['current_price'])} ({ch:+.1f}%)")

valid = [c for c in coins if c.get("price_change_percentage_24h") is not None]
gainer = max(valid, key=lambda c: c["price_change_percentage_24h"])
loser = min(valid, key=lambda c: c["price_change_percentage_24h"])

# --- Fear & Greed ---
try:
    fg = get_json("https://api.alternative.me/fng/")["data"][0]
    fg_line = f"😨 Fear & Greed: {fg['value']}/100 ({fg['value_classification']})"
except Exception:
    fg_line = "😨 Fear & Greed: unavailable"

# --- Headline ---
try:
    root = ET.fromstring(get("https://cointelegraph.com/rss"))
    item = root.find("./channel/item")
    headline = f"📰 {item.find('title').text.strip()}\n{item.find('link').text.strip()}"
except Exception:
    headline = "📰 Headline unavailable today"

today = datetime.now(timezone.utc).strftime("%d %b %Y")
msg = (
    f"📊 Crypto Daily Snapshot, {today}\n\n"
    + "\n".join(lines)
    + f"\n\n{fg_line}\n\n"
    + f"🚀 Top gainer (top 100): {gainer['symbol'].upper()} {gainer['price_change_percentage_24h']:+.1f}%\n"
    + f"💥 Top loser (top 100): {loser['symbol'].upper()} {loser['price_change_percentage_24h']:+.1f}%\n\n"
    + f"{headline}\n\n"
    + "Not financial advice. #crypto #bitcoin"
)

print(msg)

# --- Post to Telegram ---
token = os.environ["TG_TOKEN"]
chat = os.environ["TG_CHAT"]
data = urllib.parse.urlencode({
    "chat_id": chat,
    "text": msg,
    "disable_web_page_preview": "true",
}).encode()
urllib.request.urlopen(
    urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data),
    timeout=20,
)
