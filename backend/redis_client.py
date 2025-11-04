import redis
import json
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Connect Redis
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_cache_key(user_id: str, query: str) -> str:
    return f"cache:{user_id}:{query.strip().lower()}"

def get_cached_response(user_id: str, query: str):
    key = get_cache_key(user_id, query)
    return redis_client.get(key)

def set_cached_response(user_id: str, query: str, response: str, ttl=3600):
    key = get_cache_key(user_id, query)
    redis_client.setex(key, ttl, response)


def get_conversation_history(user_id: str, limit=5):
    history_key = f"history:{user_id}"
    messages = redis_client.lrange(history_key, -limit*2, -1)  # lấy N câu gần nhất
    return [json.loads(m) for m in messages]

def add_message_to_history(user_id: str, role: str, content: str):
    history_key = f"history:{user_id}"
    redis_client.rpush(history_key, json.dumps({"role": role, "content": content}))
    redis_client.ltrim(history_key, -20, -1)  # giữ tối đa 20 dòng hội thoại
