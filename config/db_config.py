from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker



ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4"
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True, future=True, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise 


