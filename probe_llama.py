import json, urllib.request
B = "https://llama-chat-worker.wj4020410.workers.dev"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def post(payload):
    r = urllib.request.Request(B + "/chat", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json", "User-Agent": UA,
                                        "Accept": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=90) as x:
            print("STATUS", x.status, "CT", x.headers.get("content-type"))
            print("BODY", x.read().decode("utf-8", "replace")[:2000])
    except Exception as e:
        print("ERR", type(e).__name__, str(e)[:200])
        try: print("BODY", e.read().decode("utf-8", "replace")[:600])
        except Exception: pass

print("===== POST /chat prompt only (browser UA) =====")
post({"prompt": "Reply in one short sentence: what is 1+1?"})
print("===== POST /chat prompt + max_tokens =====")
post({"prompt": "请用一句话总结：沪深300今日4008点，宏观LSI 18bp处于正常区间。", "max_tokens": 120})
print("===== POST /chat with messages field too =====")
post({"prompt": "你好", "messages": [{"role": "user", "content": "你好"}], "max_tokens": 60})
