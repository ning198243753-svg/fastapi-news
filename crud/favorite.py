
from starlette import status
from fastapi import HTTPException
from sqlalchemy import ReturnsRows, func, null, select,delete
from crud import news
from models.favorite import Favorite
from models.news import news

from sqlalchemy.ext.asyncio import AsyncSession


async def is_news_favorite(session:AsyncSession,user_id:int,news_id:int):
    stmt=select(Favorite).where(Favorite.user_id==user_id,Favorite.news_id==news_id)
    result=await session.execute(stmt)
    return bool(result.scalars().one_or_none())

async def add_favorite(session:AsyncSession,user_id:int,news_id:int):
    favorite_data=Favorite(user_id=user_id,news_id=news_id)
    if await is_news_favorite(session,user_id,news_id):
        return None
    session.add(favorite_data)
    await session.flush()                       # 先真正写进库（事务内），拿到自增 id
    await session.refresh(favorite_data)        # 再读回数据库生成的值（created_at 等）
    return favorite_data

async def remove_favorite(session:AsyncSession,user_id:int,news_id:int):
    stmt=delete(Favorite).where(Favorite.user_id==user_id,Favorite.news_id==news_id)
    result=await session.execute(stmt)   
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="没找到该收藏")
    return bool(result.rowcount)

async def get_favorite_list(session:AsyncSession,user_id:int,page:int,pagesize:int):
    count=select(func.count()).where(Favorite.user_id==user_id)
    count_result=await session.execute(count)
    total=count_result.scalar_one()
    query=select(news,Favorite.id.label("favorite_id"),Favorite.created_at.label("favorite_time")).join(Favorite,Favorite.news_id==news.id).where(Favorite.user_id==user_id).offset((page-1)*pagesize).limit(pagesize)
    query_result=await session.execute(query)
    rows=query_result.all()
    return rows,total

async def clear_favorite(session:AsyncSession,user_id:int):
    stmt=delete(Favorite).where(Favorite.user_id==user_id)
    result=await session.execute(stmt)
    return result.rowcount

