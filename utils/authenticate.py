from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from models.users import user
from config.db_config import get_session
from config.redis_config import get_redis
from crud.users import get_user_by_token
from starlette import status


async def get_current_user(
        authorization:str =Header(...,alias="Authorization"),
        session:AsyncSession=Depends(get_session),
        redis:Redis=Depends(get_redis),
):
    token=authorization.replace("Bearer ","")
    user=await get_user_by_token(token,session,redis)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="无效的令牌或者已过期")
    return user
  




        
    
