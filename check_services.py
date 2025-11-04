import requests
import psycopg2
from psycopg2 import OperationalError

# ======== CONFIG ========= #
SERVICES = {
    "postgres": {
        "type": "db",
        "host": "localhost",
        "port": 56432,
        "user": "admin",
        "password": "admin123",
        "dbname": "mydb",
    },
    "qdrant": {
        "type": "http",
        "url": "http://localhost:56333/healthz",
    },
    "loki": {
        "type": "http",
        "url": "http://localhost:56310/loki/api/v1/status/buildinfo",
    },
    "grafana": {
        "type": "http",
        "url": "http://localhost:56300/api/health",
    },
    "ollama": {
        "type": "http",
        "url": "http://localhost:56800/api/tags",
    }
}

# ======== CHECKERS ========= #
def check_http_service(name, url):
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            print(f"✅ {name}: OK ({url})")
        else:
            print(f"⚠️ {name}: HTTP {res.status_code} - {url}")
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__} - {e}")

def check_postgres(cfg):
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            dbname=cfg["dbname"],
            connect_timeout=3
        )
        conn.close()
        print("✅ Postgres: Connected successfully")
    except OperationalError as e:
        print(f"❌ Postgres: {e}")

# ======== RUN ========= #
if __name__ == "__main__":
    print("🔍 Checking all Docker services...\n")

    for name, cfg in SERVICES.items():
        if cfg["type"] == "http":
            check_http_service(name, cfg["url"])
        elif cfg["type"] == "db":
            check_postgres(cfg)

    print("\n✅ Done checking all services!")
