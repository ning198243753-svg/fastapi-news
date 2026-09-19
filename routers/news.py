from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_session
from config.redis_config import get_redis
from crud import news

router = APIRouter(prefix="/api/news", tags=["news"])
@router.get("/categories")
async def get_news_categories(
    session: AsyncSession = Depends(get_session), skip: int = 1, limit: int = 10,redis:Redis=Depends(get_redis)):
    
    categories = await news.get_news_categories(session, skip, limit,redis=redis)
    return {
        "code": 200,
        "message": "success",
        "data": categories
        }

@router.get("/list")
async def get_news_list(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
    categoryID: int = Query(..., gt=0, alias="categoryId"),
    page: int = Query(..., ge=1),
    pagesize: int = Query(10, ge=1, le=100, alias="pageSize"),
):
    data = await news.get_news_list(session, categoryID, page, pagesize, redis)
    return {
        "code": 200,
        "message": "success",
        "data": data
        }

@router.get("/detail")
async def get_news_detail(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
    id: int = Query(..., gt=0),
):
    data = await news.get_news_detail(session, id, redis)
    if not data:
        raise HTTPException(status_code=404, detail="News not found")

    # 浏览量 +1（写操作，不能放进缓存）
    views = await news.increment_news_views(session, id)
    if not views:
        raise HTTPException(status_code=404, detail="Failed to increment views")

    # 让本次响应里的 views 是 +1 后的值
    data["views"] = await news.get_news_views(session, id)
    return {
        "code": 200,
        "message": "success",
        "data": data,
        }