import os, json, urllib.request, urllib.error

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
