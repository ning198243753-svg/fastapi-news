from unittest import result

from fastapi import Depends, Query
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from models.history import History
from schemas.history import HistoryAddRequest, HistoryAddResponse, HistoryListResponse
from utils.authenticate import get_current_user
from config.db_config import get_session
from models.users import user
from utils.reseponse import sucess_response
from crud import history

router=APIRouter(prefix="/api/history",tags=["history"])

@router.post("/add")
async def add_history(news_data:HistoryAddRequest,session:AsyncSession=Depends(get_session),user:user=Depends(get_current_user)):
    result=await history.add_history(session,user.id,news_data.news_id)
    return sucess_response(data=HistoryAddResponse.model_validate(result),message="添加成功")  

@router.get("/list")
async def get_history_list(
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user),
    page:int=Query(1,ge=1),
    pagesize:int=Query(10,ge=1,le=100,alias="pageSize")
):
    rows,total=await history.get_history_list(session,user.id,page,pagesize)
    history_list=[{**news.__dict__,
                   "view_time":view_time
                   } for news,view_time in rows]
    hasmore=total>page*pagesize
    return sucess_response(data=HistoryListResponse(list=history_list,total=total,has_more=hasmore),message="查询成功")

@router.delete("/delete/{history_id}")
async def remove_history(
    history_id:int,
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user)
):
    result=await history.remove_history(session,user.id,history_id) 
    return sucess_response(message=f"删除{result}条历史记录")


@router.delete("/clear")
async def clear_history(
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user)
):
    count  = await history.clear_history(session,user.id)
    return sucess_response(message=f"清空{count}条数据")