
from sqlalchemy import delete, func,select
from sqlalchemy.ext.asyncio import AsyncSession
from models.history import History
from models.news import news

async def add_history(session:AsyncSession,user_id:int,news_id:int):
    query=select(History).where(History.user_id==user_id,History.news_id==news_id)
    result=await session.execute(query)
    record=result.scalars().first()      # ← 只取一次！Result.first() 会关闭 result，重复取会报 ResourceClosedError
    if record:                          # 已经浏览过 → 只更新时间
        record.view_time=func.now()
        await session.flush()
        await session.refresh(record)
        return record
    record=History(user_id=user_id,news_id=news_id)     # 第一次浏览 → 新增
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record

async def get_history_list(session:AsyncSession,user_id:int,page:int,pagesize:int):
    query=select(news,History.view_time).join(History,news.id==History.news_id).where(History.user_id==user_id).order_by(History.view_time.desc()).offset((page-1)*pagesize).limit(pagesize)
    result=await session.execute(query)
    rows=result.all()
    result=await session.execute(select(func.count(news.id)).join(History,news.id==History.news_id).where(History.user_id==user_id))
    total=result.scalar_one()
    return rows,total

async def remove_history(session:AsyncSession,user_id:int,history_id:int):
    dl=delete(History).where(History.id==history_id,History.user_id==user_id)
    result=await session.execute(dl)
    count=result.rowcount
    if count==0:
        raise Exception("删除失败")
    return count

async def clear_history(session:AsyncSession,user_id:int):
    dl=delete(History).where(History.user_id==user_id)
    result=await session.execute(dl)
    count=result.rowcount
    if count==0:
        raise Exception("删除失败")
    return count