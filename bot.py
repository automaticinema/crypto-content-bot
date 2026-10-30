import os, json, sys, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone

def tg_send(chat_id, text, reply_markup=None):
    token = os.environ.get("TG_TOKEN", "")
    if not token or not chat_id:
        print(f"TG SKIP: token set={bool(token)}, chat_id set={bool(chat_id)}")
        return False
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print("TG OK:", r.status)
            return True
    except urllib.error.HTTPError as e:
        print("TG FAIL:", e.code, e.read().decode())
        return False
    except Exception as e:
        print("TG ERROR:", e)
        return False

COINS = [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL")]

def get_prices():
    ids = ",".join(c for c, _ in COINS)
    url = ("https://api.coingecko.com/api/v3/simple/price?ids=" + ids +
           "&vs_currencies=usd&include_24hr_change=true")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def fmt_price(p):
    return f"${p:,.0f}" if p >= 100 else f"${p:,.2f}"

def build_lines(data):
    lines = []
    for cid, sym in COINS:
        d = data.get(cid)
        if not d:
            continue
        ch = d.get("usd_24h_change") or 0.0
        dot = "🟢" if ch >= 0 else "🔴"
        lines.append(f"{dot} {sym} {fmt_price(d['usd'])} ({ch:+.1f}% 24h)")
    return lines

def main():
    chat = os.environ.get("TG_CHAT", "")
    me = os.environ.get("TG_ME", "")
    try:
        data = get_prices()
    except Exception as e:
        print("PRICE FETCH FAILED:", e)
        sys.exit(1)

    lines = build_lines(data)
    if not lines:
        print("NO PRICE DATA:", data)
        sys.exit(1)

    day = datetime.now(timezone.utc).strftime("%b %d")
    post = f"📊 Crypto daily, {day}\n\n" + "\n".join(lines) + "\n\nNot financial advice."
    ok = tg_send(chat, post)

    tweet = f"Crypto daily {day}: " + " | ".join(l[2:] for l in lines) + " #crypto #bitcoin"
    intent = "https://twitter.com/intent/tweet?text=" + urllib.parse.quote(tweet)
    markup = {"inline_keyboard": [[{"text": "Post to X", "url": intent}]]}
    tg_send(me, "X draft:\n\n" + tweet, markup)

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
