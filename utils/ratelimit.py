"""简单的限流工具（固定窗口计数）

原理：
    key = f"ratelimit:{name}:{identifier}:{当前时间窗}"
    每次请求 INCR 这个 key：
        - 第 1 次 INCR 返回 1  → 顺便设置 TTL（窗口长度）
        - 返回 > limit       → 超过限制，拒绝
    INCR 是 Redis 的原子操作，所以并发下也不会算错。

优点：简单、原子、不占内存
缺点：窗口边界可能略超（例如 1 分钟窗口，在 59 秒和 61 秒各来 limit 次，会有 2 倍突发）
      对"防刷钱"这种场景完全够用；要更精确得用滑动窗口/令牌桶。
"""

import time

from fastapi import HTTPException, status
from redis import Redis


async def check_rate_limit(
    redis: Redis,
    name: str,              # 限流的业务名，如 "ai_chat"
    identifier: str,        # 限流的对象，如用户 id
    limit: int,             # 窗口内最多多少次
    window: int = 60,       # 窗口长度（秒）
):
    """超过限制就抛 429；否则放行并计数 +1

    :raises HTTPException: 429 Too Many Requests（带 Retry-After 头）
    """
    # 用"当前时间 // 窗口"作为窗口编号，窗口一换，key 自然就变了
    window_id = int(time.time()) // window
    key = f"ratelimit:{name}:{identifier}:{window_id}"

    count = await redis.incr(key)

    # 第一次访问这个 key 时，设置过期时间（避免 key 永久堆积）
    if count == 1:
        await redis.expire(key, window)

    if count > limit:
        # 距离下个窗口还有多少秒（告诉客户端什么时候可以重试）
        retry_after = window - (int(time.time()) % window)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求太频繁，请 {retry_after} 秒后再试（限制：每 {window} 秒 {limit} 次）",
            headers={"Retry-After": str(retry_after)},
        )


async def get_remaining(redis: Redis, name: str, identifier: str, limit: int, window: int = 60) -> int:
    """查当前窗口还剩多少次（可选：用来给前端展示）"""
    window_id = int(time.time()) // window
    key = f"ratelimit:{name}:{identifier}:{window_id}"
    used = await redis.get(key)
    used = int(used) if used else 0
    return max(0, limit - used)
