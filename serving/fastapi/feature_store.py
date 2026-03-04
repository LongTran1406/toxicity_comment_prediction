import redis
import json

r = redis.Redis(host="redis", port=6379, decode_responses=True)

def get_features(comment_id: str):
    data = r.hgetall(f"comment:{comment_id}")
    if data:
        return {
            "comment_text": data["comment_text"]
        }
    return None