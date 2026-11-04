import json, urllib.request
B = "https://llama-chat-worker.wj4020410.workers.dev"

def post(payload):
    r = urllib.request.Request(B + "/chat", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            print("STATUS", x.status, "CT", x.headers.get("content-type"))
            print("BODY", x.read().decode("utf-8", "replace")[:1500])
    except Exception as e:
        print("ERR", type(e).__name__, str(e)[:200])
        try: print("BODY", e.read().decode("utf-8", "replace")[:600])
        except Exception: pass

print("===== GET / =====")
try:
    with urllib.request.urlopen(B + "/", timeout=20) as x:
        print(x.read().decode("utf-8", "replace")[:2500])
except Exception as e:
    print("ERR", str(e)[:200])

print("===== POST /chat prompt only =====")
post({"prompt": "Reply in one short sentence: what is 1+1?"})

print("===== POST /chat prompt + max_tokens =====")
post({"prompt": "用一句话总结：沪深300今日4008点，宏观LSI 18bp正常。", "max_tokens": 120})

print("===== POST /chat with system+user keys =====")
post({"prompt": "你好", "system": "You are concise.", "temperature": 0.2})
