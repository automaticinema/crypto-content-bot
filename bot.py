import os, json, sys, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone

def tg_send(chat_id, text, reply_markup=None):
    token = os.environ.get("TG_TOKEN", "")
    if not token or not chat_id:
        print(f"TG SKIP: token set={bool(token)}, chat_id set={bool(chat_id)}")
        return False
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
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

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

MAJORS = [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL")]
STABLES = {"usdt", "usdc", "dai", "usde", "fdusd", "tusd", "usds", "pyusd", "usdd"}

def get_market():
    url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
           "&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h")
    return get_json(url)

def get_fng():
    try:
        d = get_json("https://api.alternative.me/fng/?limit=1")["data"][0]
        return int(d["value"]), d["value_classification"]
    except Exception as e:
        print("FNG FAILED:", e)
        return None

def fng_emoji(v):
    if v <= 25: return "😱"
    if v <= 45: return "😨"
    if v <= 55: return "😐"
    if v <= 75: return "😀"
    return "🤑"

def fmt_price(p):
    return f"${p:,.0f}" if p >= 100 else f"${p:,.2f}"

def main():
    chat = os.environ.get("TG_CHAT", "")
    me = os.environ.get("TG_ME", "")

    try:
        market = get_market()
    except Exception as e:
        print("MARKET FETCH FAILED:", e)
        sys.exit(1)

    by_id = {c["id"]: c for c in market}
    price_lines, tweet_parts = [], []
    for cid, sym in MAJORS:
        c = by_id.get(cid)
        if not c or c.get("current_price") is None:
            continue
        ch = c.get("price_change_percentage_24h") or 0.0
        dot = "🟢" if ch >= 0 else "🔴"
        price_lines.append(f"{dot} {sym}: {fmt_price(c['current_price'])} ({ch:+.1f}%)")
        tweet_parts.append(f"{sym} {fmt_price(c['current_price'])} ({ch:+.1f}%)")
    if not price_lines:
        print("NO PRICE DATA")
        sys.exit(1)

    movers = [c for c in market
              if c.get("price_change_percentage_24h") is not None
              and c["symbol"].lower() not in STABLES]
    movers.sort(key=lambda c: c["price_change_percentage_24h"])
    loser, gainer = (movers[0], movers[-1]) if movers else (None, None)

    fng = get_fng()

    day = datetime.now(timezone.utc).strftime("%b %d")
    body = [f"📊 Crypto Daily | {day}", ""] + price_lines + [""]
    tweet = f"Crypto daily {day}: " + " | ".join(tweet_parts)

    if fng:
        v, label = fng
        fng_line = f"{fng_emoji(v)} Fear & Greed: {v}/100 ({label})"
        body.append(fng_line)
        tweet += f"\n{fng_line}"
    if gainer and loser:
        mv = (f"🚀 {gainer['symbol'].upper()} {gainer['price_change_percentage_24h']:+.1f}%"
              f" | 💥 {loser['symbol'].upper()} {loser['price_change_percentage_24h']:+.1f}%")
        body.append(mv)
        tweet += f"\n{mv}"

    body += ["", "#crypto #bitcoin", "", "Not financial advice."]
    tweet += "\n#crypto #bitcoin"

    ok = tg_send(chat, "\n".join(body))

    intent = "https://twitter.com/intent/tweet?text=" + urllib.parse.quote(tweet)
    markup = {"inline_keyboard": [[{"text": "Post to X", "url": intent}]]}
    tg_send(me, "X draft:\n\n" + tweet, markup)

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
