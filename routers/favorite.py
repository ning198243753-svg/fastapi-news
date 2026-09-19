from itertools import count

from fastapi import APIRouter,Depends,Query
from config.db_config import get_session
from crud import users,favorite
from models.news import news
from models.users import user
from models.favorite import Favorite
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.favorite import FavoriteAddRequest, FavoriteAddResponse, FavoriteCheckResponse, FavoriteListResponse
from utils.authenticate import get_current_user
from utils.reseponse import sucess_response



router=APIRouter(prefix="/api/favorite",tags=["favorite"])

@router.get("/check")
async def check_favorite(
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user),
    news_id:int=Query(...,gt=0,alias="newsId")
):
    is_favorite=await favorite.is_news_favorite(session,user.id,news_id)
    return sucess_response(data=FavoriteCheckResponse(is_favorite=is_favorite),message="查询成功")

@router.post("/add")
async def add_favorite(
    news_id:FavoriteAddRequest,
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user)
    
):
    favorite_data=await favorite.add_favorite(session,user.id,news_id.news_id)
    if favorite_data is None:
        return sucess_response(message="添加失败")
    return sucess_response(data=FavoriteAddResponse.model_validate(favorite_data),message="添加成功")

@router.delete("/remove")
async def remove_favorite(
    news_id:FavoriteAddRequest=Query(...,alias="newsId"),
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user)
):
    if not await favorite.remove_favorite(session,user.id,news_id.news_id):
        return sucess_response(message="删除失败")
    return sucess_response(message="删除成功")

@router.get("/list")
async def get_favorite_list(
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user),
    page:int=Query(...,ge=1),
    pagesize:int=Query(10,ge=1,le=100,alias="pageSize")
):
    rows,total=await favorite.get_favorite_list(session,user.id,page,pagesize)
    favorite_list=[{
        **news.__dict__ ,
        "favorite_time":favorite_time,
        "favorite_id":favorite_id
    } for news,favorite_id,favorite_time in rows]
    has_more=total> page*pagesize

    return sucess_response(data=FavoriteListResponse(list=favorite_list,total=total,has_more=has_more),message="查询成功")


@router.delete("/clear")
async def clear_favorite(
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user)
):
    count  = await favorite.clear_favorite(session,user.id)
    return sucess_response(message=f"清空{count}条数据")