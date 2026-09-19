from redis import Redis
from sqlalchemy import select,func, update
from models.news import news_category ,news
from sqlalchemy.ext.asyncio import AsyncSession

from utils.cache import get_cache, set_cache, delete_cache

# ---------- 缓存 key 的统一定义（改 key 只改这里）----------
def key_categories(skip: int, limit: int) -> str:
    return f"news:categories:{skip}:{limit}"

def key_list(category_id: int, page: int, pagesize: int) -> str:
    return f"news:list:cat:{category_id}:page:{page}:size:{pagesize}"

def key_detail(news_id: int) -> str:
    return f"news:detail:{news_id}"

# ---------- 统一的“ORM 对象 → 前端要的 dict”转换 ----------
def news_to_dict(n) -> dict:
    """新闻列表项（前端用 camelCase）"""
    return {
        "id": n.id,
        "title": n.title,
        "description": n.description,
        "image": n.image,
        "author": n.author,
        "categoryId": n.category_id,
        "views": n.views,
        "publishTime": n.publish_time.isoformat() if n.publish_time else None,
    }

async def get_news_categories(session: AsyncSession, skip: int, limit: int, redis: Redis):
    redis_key = key_categories(skip, limit)
    ttl = 86400                                  # 分类几乎不变 → 缓存 1 天

    cache_data = await get_cache(redis_key, redis)
    if cache_data is not None:
        return cache_data

    result = await session.execute(select(news_category).offset((skip-1)*limit).limit(limit))
    rows = result.scalars().all()
    cache_data = [{
        "id": row.id,
        "name": row.name,
        "sort_order": row.sort_order,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None
    } for row in rows]

    await set_cache(redis_key, cache_data, redis, ttl)
    return cache_data

async def get_news_list(session: AsyncSession, categoryID: int, page: int, pagesize: int, redis: Redis):
    """新闻列表（含 total 和 has_more），整体缓存，保证 list/total 是同一时刻的数据"""
    redis_key = key_list(categoryID, page, pagesize)
    ttl = 120                                    # 列表变化快 → 2 分钟

    cache_data = await get_cache(redis_key, redis)
    if cache_data is not None:
        return cache_data

    skip = (page - 1) * pagesize
    result = await session.execute(select(news).where(news.category_id == categoryID).offset(skip).limit(pagesize))
    rows = result.scalars().all()

    total = await get_num_by_category_id(session, categoryID)
    has_more = skip + len(rows) < total

    cache_data = {
        "list": [news_to_dict(n) for n in rows],
        "total": total,
        "has_more": has_more,
    }

    await set_cache(redis_key, cache_data, redis, ttl)
    return cache_data

async def get_news_detail(session: AsyncSession, news_id: int, redis: Redis):
    """新闻详情：只缓存“不变的部分”（内容 + 相关新闻）；浏览量每次实时读，否则浏览量就不涨了"""
    redis_key = key_detail(news_id)
    ttl = 600                                    # 10 分钟

    cache_data = await get_cache(redis_key, redis)

    if cache_data is None:
        # 未命中 → 查库（浏览量的 +1 由 router 负责，这里不动）
        news_detail = await get_news_by_id(session, news_id)
        if not news_detail:
            return None

        related_news = await get_related_news(session, news_detail.category_id, news_detail.id, limit=5)
        cache_data = {
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time.isoformat() if news_detail.publish_time else None,
            "categoryId": news_detail.category_id,
            "relatedNews": related_news,
        }
        await set_cache(redis_key, cache_data, redis, ttl)

    # 浏览量：每次实时查（不缓存）
    cache_data["views"] = await get_news_views(session, news_id)
    return cache_data

async def get_news_views(session: AsyncSession, news_id: int) -> int:
    result = await session.execute(select(news.views).where(news.id == news_id))
    return result.scalar_one_or_none() or 0

async def get_num_by_category_id(session: AsyncSession, category_id: int):
    result = await session.execute(select(func.count(news.id)).where(news.category_id == category_id))
    return result.scalars().one_or_none()

async def get_news_by_id(session: AsyncSession, news_id: int):
    result = await session.execute(select(news).where(news.id == news_id))
    return result.scalars().one_or_none()

async def increment_news_views(session: AsyncSession, news_id: int):
    stmt=update(news).where(news.id == news_id).values(views=news.views + 1).execution_options(synchronize_session="fetch")
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

async def clear_news_cache(redis: Redis, news_id: int):
    """新闻数据变了之后调用：删掉详情缓存（列表缓存靠 TTL 自然过期）

    注意：Redis 的 DEL 不支持通配符，所以这里只删“确定的 key”。
    如果以后要按前缀批量删，需要用 SCAN 逐个收集再 DEL。
    """
    await delete_cache(redis, key_detail(news_id))

async def get_related_news(session: AsyncSession, category_id: int,news_id: int, limit: int ):
    result = await session.execute(
        select(news)
        .where(news.category_id == category_id, news.id != news_id)
        .order_by(news.publish_time.desc(),news.views.desc())
        .limit(limit)
    )
    result_list = result.scalars().all()
    return [news_to_dict(n) for n in result_list]