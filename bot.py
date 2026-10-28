import os, json, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read()


def arrow(x):
    return "🟢" if x >= 0 else "🔴"


# --- Prices (CoinGecko, top 100 by market cap) ---
url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=24h"
coins = json.loads(get(url))
by_id = {c["id"]: c for c in coins}

price_lines = []
for cid, sym in [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL")]:
    c = by_id.get(cid)
    if c:
        ch = c["price_change_percentage_24h"] or 0
        price_lines.append(f"{arrow(ch)} {sym}: ${c['current_price']:,.2f} ({ch:+.2f}%)")

# --- Top gainer / loser (skip stablecoins and extreme outliers) ---
stables = ("usdt", "usdc", "dai", "usde", "fdusd", "usds", "pyusd")
movers = [c for c in coins if c.get("price_change_percentage_24h") is not None and abs(c["price_change_percentage_24h"]) < 1000 and c["symbol"].lower() not in stables]
gainer = max(movers, key=lambda c: c["price_change_percentage_24h"])
loser = min(movers, key=lambda c: c["price_change_percentage_24h"])

# --- Fear & Greed ---
try:
    fg = json.loads(get("https://api.alternative.me/fng/"))["data"][0]
    fg_line = f"😨 Fear & Greed: {fg['value']}/100 ({fg['value_classification']})"
except Exception:
    fg_line = "😨 Fear & Greed: n/a"

# --- Headline (CoinDesk RSS) ---
try:
    root = ET.fromstring(get("https://www.coindesk.com/arc/outboundfeeds/rss/"))
    item = root.find("./channel/item")
    head = "📰 " + item.find("title").text + "\n" + item.find("link").text
except Exception:
    head = "📰 Headline: n/a"

# --- Build message ---
date = datetime.now(timezone.utc).strftime("%d %b %Y")
g_pct = format(gainer["price_change_percentage_24h"], "+.1f")
l_pct = format(loser["price_change_percentage_24h"], "+.1f")
movers_line = "🚀 Top gainer: " + gainer["symbol"].upper() + " " + g_pct + "%\n💥 Top loser: " + loser["symbol"].upper() + " " + l_pct + "%"

parts = []
parts.append("📊 Crypto Daily – " + date)
parts.append("\n".join(price_lines))
parts.append(movers_line)
parts.append(fg_line)
parts.append(head)
parts.append("Not financial advice. DYOR.")
parts.append("#crypto #bitcoin #ethereum #solana")
text = "\n\n".join(parts)
print(text)

# --- Post to Telegram ---
token = os.environ.get("TG_TOKEN")
chat = os.environ.get("TG_CHAT")
if token and chat:
    data = urllib.parse.urlencode({"chat_id": chat, "text": text, "disable_web_page_preview": "true"}).encode()
    tg_url = "https://api.telegram.org/bot" + token + "/sendMessage"
    resp = urllib.request.urlopen(tg_url, data, timeout=20)
    print(resp.read())
else:
    print("TG_TOKEN / TG_CHAT not set, skipping Telegram post")

print("Done")
