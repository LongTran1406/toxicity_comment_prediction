import redis
import json
import os

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

def get_features(comment_id: str):
    data = r.hgetall(f"comment:{comment_id}")
    if data:
        return {
            "comment_text": data["comment_text"]
        }
    return None