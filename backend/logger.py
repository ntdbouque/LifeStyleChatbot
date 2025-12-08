import requests, json, time, os

LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")

def log_to_loki(user_id: str, query: str, response: str, model: str = "mistral"):
    timestamp_ns = str(time.time_ns())
    entry = {
        "streams": [
            {
                "stream": {
                    "app": "chatbot",
                    "user": user_id,
                    "model": model
                },
                "values": [
                    [timestamp_ns, json.dumps({
                        "query": query,
                        "response": response
                    })]
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    try:
        res = requests.post(f"{LOKI_URL}/loki/api/v1/push", headers=headers, json=entry, timeout=2)
        if res.status_code != 204:
            print(f"[WARN] Loki push failed ({res.status_code}): {res.text}")
        else:
            print("[OK] Log pushed to Loki ✅")
    except Exception as e:
        print(f"[ERROR] Loki logging error: {e}")
