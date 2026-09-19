from redis.asyncio import Redis,ConnectionPool

REDIS_URL = "redis://localhost:6379/0"
_pool = ConnectionPool.from_url(REDIS_URL,decode_responses=True,max_connections=20)

def get_redis() -> Redis:
    return Redis(connection_pool=_pool)
