
import json
from redis import Redis

# ---------- 缓存 key 的统一定义 ----------
def key_auth_token(token: str) -> str:
    return f"auth:token:{token}"

async def get_cache(key:str,redis:Redis):
    raw_data=await redis.get(key)
    return json.loads(raw_data) if raw_data else None

async def set_cache(key:str,value:dict,redis:Redis,ttl:int=300):
    await redis.set(key,json.dumps(value,ensure_ascii=False,default=str),ex=ttl)

async def delete_cache(redis:Redis,*keys:str):
    if keys:
        await redis.delete(*keys)
