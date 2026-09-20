import os

from dotenv import load_dotenv
from redis.asyncio import Redis, ConnectionPool

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 进程级连接池（在 lifespan 里创建 / 关闭更规范，这里用模块级也够用）
_pool = ConnectionPool.from_url(REDIS_URL, decode_responses=True, max_connections=20)


def get_redis() -> Redis:
    """FastAPI 依赖：拿一个共享连接池里的客户端（不新建连接）"""
    return Redis(connection_pool=_pool)


async def close_redis() -> None:
    """应用关闭时调用：释放连接池"""
    await _pool.disconnect()


async def ping_redis() -> bool:
    """启动时自检：Redis 连得上吗"""
    client = Redis(connection_pool=_pool)
    try:
        return await client.ping()
    finally:
        await client.aclose()
