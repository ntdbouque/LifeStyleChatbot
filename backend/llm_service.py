# backend/llm_service.py
import requests
import os
import json

OLLAMA_URL = os.getenv("LLM_API_BASE", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral")

def call_llm(prompt: str) -> str:
    """
    Gọi LLM self-host qua Ollama API (hỗ trợ cả stream NDJSON và full JSON)
    """
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        # ép tắt stream nếu bạn muốn gọn, 
        # hoặc bỏ dòng này để giữ stream (và đọc iter_lines bên dưới)
        "stream": True  
    }

    try:
        # stream=True để đọc NDJSON từng dòng
        with requests.post(f"{OLLAMA_URL}/api/generate", json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()

            # Nếu stream NDJSON
            if response.headers.get("content-type", "").startswith("application/x-ndjson"):
                full_text = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line.decode("utf-8"))
                        # Gom từng token trong field "response"
                        if "response" in obj:
                            full_text += obj["response"]
                    except json.JSONDecodeError:
                        continue
                return full_text.strip()
            else:
                # Nếu không stream (trả full JSON)
                data = response.json()
                return data.get("response", "").strip()

    except requests.exceptions.RequestException as e:
        print(f"[LLM ERROR] {e}")
        return "[Error] Không thể kết nối tới LLM server."
