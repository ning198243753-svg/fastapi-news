import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import async_engine, get_session
from config.redis_config import close_redis, get_redis, ping_redis
from routers import ai, news, users, favorite, history
from utils.exception_register import exception_handler_register

logger = logging.getLogger(__name__)


# ============================================================
#  lifespan：应用"启动时"和"关闭时"各执行一次
#    yield 之前 → 启动（准备全局资源）
#    yield 之后 → 关闭（释放全局资源）
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------- 启动 ----------
    try:
        ok = await ping_redis()
        logger.info("Redis 连接正常: %s", ok)
    except Exception as e:
        # 启动自检失败不直接退出（Redis 挂了应用还是能跑，只是没缓存）
        logger.warning("Redis 连接失败（缓存会不可用）: %s", e)

    logger.info("应用启动完成")
    yield

    # ---------- 关闭 ----------
    logger.info("应用正在关闭，释放资源...")
    await close_redis()             # 释放 Redis 连接池
    await async_engine.dispose()    # 释放数据库连接池
    logger.info("资源已释放")


app = FastAPI(lifespan=lifespan)

exception_handler_register(app)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],allow_credentials=True)

app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(ai.router)


# ============================================================
#  健康检查：给负载均衡 / K8s / Docker 探活用
#    依赖正常 → 200，依赖有问题 → 503
# ============================================================
@app.get("/health", tags=["system"])
async def health(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    checks = {}

    try:
        await session.execute(text("SELECT 1"))
        checks["mysql"] = "ok"
    except Exception as e:
        checks["mysql"] = f"error: {type(e).__name__}"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"

    ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ok" if ok else "degraded", "checks": checks},
    )
