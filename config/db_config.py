import os
import sys

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

load_dotenv()

# 数据库连接串只从 .env 读取（★ 不要写默认值/兜底密码，否则缺配置时会静默用错库）
# 格式：mysql+aiomysql://用户名:密码@主机:端口/库名?charset=utf8mb4
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL")
if not ASYNC_DATABASE_URL:
    # fail fast：缺配置就立刻报错，而不是带着错误配置继续跑
    sys.exit("❌ 环境变量 DATABASE_URL 没读到，请检查 .env 文件（参考 .env.example）")

# echo=True 会把每条 SQL 打到控制台，开发时方便、上线要关掉
DB_ECHO = os.getenv("DB_ECHO", "true").lower() == "true"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=DB_ECHO,
    future=True,
    pool_size=10,
    max_overflow=20,
    # ★ 连接回收：连接存活超过 1 小时就重建（MySQL 默认 8 小时会断开空闲连接，
    #   不配这个会出现"服务跑几小时后突然 Lost connection"）
    pool_recycle=3600,
    # ★ 取连接前先探测一下是否还活着（防网络抖动 / MySQL 重启导致的死连接）
    pool_pre_ping=True,
    # 取连接最多等 30 秒
    pool_timeout=30,
)

async_session = async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)


async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
