import json, urllib.request, urllib.parse, datetime, os

COINS = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}
url = ("https://api.coingecko.com/api/v3/simple/price?ids="
       + ",".join(COINS) + "&vs_currencies=usd&include_24hr_change=true")
data = json.load(urllib.request.urlopen(url))

lines = []
for cid, sym in COINS.items():
    price = data[cid]["usd"]
    chg = data[cid]["usd_24h_change"]
    arrow = "🟢" if chg >= 0 else "🔴"
    lines.append(f"{arrow} {sym}: ${price:,.2f} ({chg:+.2f}% 24h)")

best = max(COINS, key=lambda c: data[c]["usd_24h_change"])
today = datetime.date.today().isoformat()
post = (f"Crypto snapshot {today}\n\n" + "\n".join(lines) +
        f"\n\nTop mover today: {COINS[best]}\n"
        "Not financial advice.\n"
        "#crypto #bitcoin")

os.makedirs("drafts", exist_ok=True)
with open(f"drafts/{today}.txt", "w", encoding="utf-8") as f:
    f.write(post)
print(post)

# Send to Telegram if the secrets are set
token = os.environ.get("TG_TOKEN")
chat = os.environ.get("TG_CHAT")
if token and chat:
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=urllib.parse.urlencode({"chat_id": chat, "text": post}).encode(),
        )
        urllib.request.urlopen(req)
        print("Sent to Telegram")
    except Exception as e:
        print("Telegram failed:", e)
else:
    print("Telegram secrets not set, skipping")
