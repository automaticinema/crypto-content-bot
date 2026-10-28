import os, json, urllib.request, urllib.parse
from datetime import datetime, timezone


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read()


url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=7d"
coins = json.loads(get(url))

stables = ("usdt", "usdc", "dai", "usde", "fdusd", "usds", "pyusd")
key = "price_change_percentage_7d_in_currency"
movers = [c for c in coins if c.get(key) is not None and abs(c[key]) < 1000 and c["symbol"].lower() not in stables]
movers.sort(key=lambda c: c[key], reverse=True)

up = ["🟢 " + c["symbol"].upper() + " " + format(c[key], "+.1f") + "%" for c in movers[:5]]
down = ["🔴 " + c["symbol"].upper() + " " + format(c[key], "+.1f") + "%" for c in movers[-5:][::-1]]

date = datetime.now(timezone.utc).strftime("%d %b %Y")
parts = []
parts.append("📅 Weekly Wrap – " + date)
parts.append("🚀 Top 5 gainers (7d)\n" + "\n".join(up))
parts.append("💥 Top 5 losers (7d)\n" + "\n".join(down))
parts.append("Not financial advice. DYOR.")
parts.append("#crypto #altcoins #weeklywrap")
text = "\n\n".join(parts)
print(text)

token = os.environ.get("TG_TOKEN")
chat = os.environ.get("TG_CHAT")
if token and chat:
    data = urllib.parse.urlencode({"chat_id": chat, "text": text, "disable_web_page_preview": "true"}).encode()
    resp = urllib.request.urlopen("https://api.telegram.org/bot" + token + "/sendMessage", data, timeout=20)
    print(resp.read())
else:
    print("TG_TOKEN / TG_CHAT not set, skipping Telegram post")

print("Done")
