# check_services.py
import os
import sys
import requests
import psycopg2
from urllib.parse import urlparse
from colorama import init, Fore, Style
import json
from configs.configs import get_config

# Khởi tạo colorama (tự động reset màu sau mỗi print)
init(autoreset=True)

# ======== LOAD CONFIG ========= #
configs = get_config('./configs/configs.yaml')

# ======== ICONS & COLORS ========= #
OK = f"{Fore.GREEN}OK{Style.RESET_ALL}"
FAIL = f"{Fore.RED}FAIL{Style.RESET_ALL}"
WARN = f"{Fore.YELLOW}WARN{Style.RESET_ALL}"
INFO = f"{Fore.CYAN}INFO{Style.RESET_ALL}"

# ======== CHECKERS ========= #
def title(text):
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}═'═'═' {text} ═'═'═'═{Style.RESET_ALL}\n")

def check_vllm_service(vllm_cfg):
    url = f"{vllm_cfg['URI'].rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {vllm_cfg.get('api_key', '')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": vllm_cfg["model_name"],
        "messages": [{"role": "user", "content": "Xin chào! Bạn khỏe không?"}],
        "max_tokens": 64,
        "temperature": 0.7
    }

    print(f"{Fore.CYAN}LLM vLLM ({vllm_cfg['model_name'][:35]}{'...' if len(vllm_cfg['model_name']) > 35 else ''})")
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=12)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].strip()
            preview = (content[:80] + "...") if len(content) > 80 else content
            print(f"   {OK} Kết nối thành công")
            print(f"   {Fore.LIGHTBLACK_EX}↳ \"{preview}\"")
        else:
            print(f"   {FAIL} HTTP {res.status_code}")
            print(f"   {Fore.RED}{res.text[:150]}")
    except Exception as e:
        print(f"   {FAIL} {type(e).__name__}: {e}")

def check_backend_service(url):
    """Check backend service with both /health and /chat endpoints (same way as frontend)"""
    base_url = url.rstrip("/")
    print(f"{Fore.BLUE}API Backend{'':<0}", end="")
    
    health_ok = False
    health_error = None
    chat_ok = False
    chat_error = None
    
    # Check /health endpoint
    try:
        r = requests.get(f"{base_url}/health", timeout=6)
        if r.status_code == 200:
            health_ok = True
        else:
            health_error = f"HTTP {r.status_code}"
    except Exception as e:
        health_error = f"{type(e).__name__}: {str(e)[:80]}"
    
    # Check /chat endpoint (POST with dummy data) - SAME WAY AS FRONTEND
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "message": "Xin chào",
            "user_id": "test_check"
        }
        # Call exactly like frontend does: stream=True, iter_content
        r = requests.post(f"{base_url}/chat", json=payload, headers=headers, stream=True, timeout=15)
        
        if r.status_code == 200:
            # Try to iterate chunks like frontend does
            try:
                full_content = ""
                for chunk in r.iter_content(chunk_size=64, decode_unicode=True):
                    if chunk:
                        full_content += chunk
                
                if full_content:
                    chat_ok = True
                else:
                    chat_error = "No content received from stream"
            except Exception as stream_err:
                chat_error = f"{type(stream_err).__name__}: {str(stream_err)[:80]}"
        else:
            try:
                body = r.text[:200]
            except:
                body = ""
            chat_error = f"HTTP {r.status_code}: {body}"
    except requests.exceptions.Timeout:
        chat_error = "Timeout (15s) - server may be processing slowly"
    except requests.exceptions.ConnectionError as e:
        chat_error = f"ConnectionError: {str(e)[:80]}"
    except Exception as e:
        chat_error = f"{type(e).__name__}: {str(e)[:80]}"
    
    # Print result
    if health_ok and chat_ok:
        print(f"{OK} {Fore.LIGHTBLACK_EX}{base_url}")
        print(f"   {Fore.LIGHTBLACK_EX}↳ /health: {OK} | /chat: {OK}")
    elif health_ok or chat_ok:
        status = f"/health: {'✓' if health_ok else '✗'} | /chat: {'✓' if chat_ok else '✗'}"
        print(f"{WARN} {Fore.LIGHTBLACK_EX}{base_url}")
        print(f"   {Fore.LIGHTBLACK_EX}↳ {status}")
        if health_error:
            print(f"   {Fore.RED}✗ /health error: {health_error}")
        if chat_error:
            print(f"   {Fore.RED}✗ /chat error: {chat_error}")
    else:
        print(f"{FAIL} {Fore.LIGHTBLACK_EX}{base_url}")
        print(f"   {Fore.LIGHTBLACK_EX}↳ Cả 2 endpoint đều không thể kết nối")
        if health_error:
            print(f"   {Fore.RED}/health: {health_error}")
        if chat_error:
            print(f"   {Fore.RED}/chat: {chat_error}")

def check_http_service(name, url):
    icon = {
        "Qdrant": "Vector DB", "Loki": "Logs", "Grafana": "Dashboard",
        "Backend": "API", "Frontend": "Web UI"
    }.get(name, "Service")
    print(f"{Fore.BLUE}{icon} {name:<8}", end="")
    try:
        r = requests.get(url.rstrip("/"), timeout=6)
        if r.status_code == 200:
            print(f"{OK} {Fore.LIGHTBLACK_EX}{url}")
        else:
            print(f"{WARN} HTTP {r.status_code}")
    except Exception as e:
        print(f"{FAIL} {str(e)[:60]}")

def check_postgres_by_uri(uri):
    print(f"{Fore.YELLOW}PostgreSQL Database")
    try:
        parsed = urlparse(uri)
        conn = psycopg2.connect(uri, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        conn.close()
        db_name = parsed.path.lstrip('/') or "unknown"
        print(f"   {OK} Kết nối thành công")
        print(f"   {Fore.LIGHTBLACK_EX}Host: {parsed.hostname}:{parsed.port} | DB: {db_name}")
        print(f"   {Fore.LIGHTBLACK_EX}Version: {version.split(',')[0]}")
    except Exception as e:
        print(f"   {FAIL} {type(e).__name__}: {e}")

# ======== RUN ========= #
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.WHITE}{Style.BRIGHT}"
          "    HỆ THỐNG GIÁM SÁT SỨC KHỎE NGƯỜI CAO TUỔI\n"
          f"{Fore.CYAN}           Kiểm tra trạng thái dịch vụ{Style.RESET_ALL}\n")

    title("1. AI ENGINE (vLLM)")
    vllm_config = configs["services"].get("vllm")
    if vllm_config and vllm_config.get("URI"):
        check_vllm_service(vllm_config)
    else:
        print(f"   {WARN} Không tìm thấy cấu hình vLLM")

    title("2. CÁC DỊCH VỤ HỆ THỐNG")
    for name in ["qdrant", "loki", "grafana", "backend", "frontend"]:
        service = configs["services"].get(name, {})
        uri = service.get("URI") if service else None
        if uri:
            if name == "backend":
                check_backend_service(uri)
            else:
                check_http_service(name.capitalize(), uri)
        else:
            print(f"{Fore.BLUE}Service {name.capitalize():<8} {WARN} Thiếu URI trong config")

    title("3. CƠ SỞ DỮ LIỆU")
    pg_config = configs["services"].get("postgres", {})
    if pg_config.get("URI"):
        check_postgres_by_uri(pg_config["URI"])
    else:
        print(f"   {FAIL} Không tìm thấy cấu hình PostgreSQL (cần URI)")

    print(f"\n{Fore.GREEN}{Style.BRIGHT}Hoàn tất kiểm tra toàn bộ hệ thống!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   Chúc một ngày làm việc hiệu quả!{Style.RESET_ALL}\n")