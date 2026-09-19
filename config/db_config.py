import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

load_dotenv()

# 数据库连接串从 .env 读取（不要把真实密码写进代码！）
# 格式：mysql+aiomysql://用户名:密码@主机:端口/库名?charset=utf8mb4
ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4",
)

# echo=True 会把每条 SQL 打到控制台，开发时方便、上线要关掉
DB_ECHO = os.getenv("DB_ECHO", "true").lower() == "true"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=DB_ECHO,
    future=True,
    pool_size=10,
    max_overflow=20,
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
