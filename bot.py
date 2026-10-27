import json, urllib.request, urllib.parse, datetime, os
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

today = datetime.date.today().isoformat()

# --- Build posts ---
x_parts = [f"Crypto check {today}", ""] + price_lines
if fg_line:
    x_parts.append(fg_line)
x_parts += [gain_line, "", "Not financial advice. #crypto #bitcoin"]
x_post = "\n".join(x_parts)
if len(x_post) > 280:  # drop the gainer line if too long
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
    f.write("=== X POST ===\n" + x_post + "\n\n=== TELEGRAM POST ===\n" + tg_post)
print(tg_post)
print(f"\n[X post length: {len(x_post)}]")

# --- Telegram ---
token = os.environ.get("TG_TOKEN")
chat = os.environ.get("TG_CHAT")
if token and chat:
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=urllib.parse.urlencode({"chat_id": chat, "text": tg_post}).encode(),
        )
        urllib.request.urlopen(req)
        print("Sent to Telegram")
    except Exception as e:
        print("Telegram failed:", e)
else:
    print("Telegram secrets not set, skipping")
