from fastapi import Depends, HTTPException
from sqlalchemy import delete, select, update
from models.users import user, UserToken
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import PasswordUpdate, UpdateUserInfo, UserRequest
from config.db_config import get_session
from utils.security import get_hash_password, verify_password
from datetime import datetime, timedelta
from starlette import status
import uuid
from types import SimpleNamespace
from redis import Redis
from utils.cache import get_cache, set_cache, delete_cache, key_auth_token

# 认证缓存存活时间（秒）。短一点：登出/改资料后最多 10 分钟就自然失效
AUTH_CACHE_TTL = 600


def user_to_cache_dict(u) -> dict:
    """只缓存“认人”需要的信息（注意：绝不缓存密码）"""
    return {
        "id": u.id,
        "username": u.username,
        "nickname": u.nickname,
        "avatar": u.avatar,
        "gender": u.gender,
        "bio": u.bio,
        "phone": u.phone,
    }

async def get_user_by_name(session: AsyncSession, userReq :UserRequest):
    stmt=select(user).where(user.username == userReq.username)
    result = await session.execute(stmt)
    return result.scalars().one_or_none()

async def user_register(session: AsyncSession, userReq :UserRequest):
    hashed_password = get_hash_password(userReq.password)
    user_data = user(username=userReq.username, password=hashed_password)
    session.add(user_data)
    await session.commit()
    await session.refresh(user_data)
    return user_data

async def create_user_token(session: AsyncSession, userid: int):
    created_token = str(uuid.uuid4())
    stmt = select(UserToken).join(user, UserToken.user_id == user.id).where(user.id == userid)
    result = await session.execute(stmt)
    user_token = result.scalars().one_or_none()
    expires_at = datetime.now() + timedelta(days=7)  # 设置过期时间为7天后

    if user_token:
        stmt = update(UserToken).where(UserToken.user_id == user_token.user_id).values(token=created_token, expires_at=expires_at)
        await session.execute(stmt)
 
    else:
       token_data = UserToken(user_id=userid, token=created_token, expires_at=expires_at)
       session.add(token_data)


    return created_token

async def authenticate_user(user_req:UserRequest,session:AsyncSession):
    searched=await get_user_by_name(session=session,userReq=user_req)
    if not searched:
        return None
    verify=verify_password(user_req.password,searched.password)
    if not verify:
        return None
    return searched

async def get_user_by_token(token:str,session:AsyncSession,redis:Redis):
    """认证：token → 用户。先查 Redis，未命中再查库（每个需登录的请求都会调它）"""
    cache_key = key_auth_token(token)

    # ① 先查缓存（命中则 0 条 SQL）
    cached = await get_cache(cache_key, redis)
    if cached is not None:
        return SimpleNamespace(**cached)      # 能 user.id / user.username 这样访问

    # ② 未命中 → 查库（原来的逻辑）
    stmt=select(UserToken).where(UserToken.token==token)
    result=await session.execute(stmt)
    db_token=result.scalar_one_or_none()
    if not db_token or db_token.expires_at < datetime.now():
        return None
    stmt=select(user).where(user.id==db_token.user_id)
    result=await session.execute(stmt)
    db_user = result.scalar_one_or_none()
    if not db_user:
        return None

    # ③ 写缓存，并返回真正的 ORM 对象
    await set_cache(cache_key, user_to_cache_dict(db_user), redis, AUTH_CACHE_TTL)
    return db_user


async def get_user_orm_by_id(session: AsyncSession, user_id: int):
    """拿真正的 ORM 对象（改密码这种需要写库的场景用，不能用缓存）"""
    stmt = select(user).where(user.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def clear_auth_cache(redis: Redis, token: str | None):
    """登出 / 改资料后调用：删掉这个 token 的认证缓存"""
    if token:
        await delete_cache(redis, key_auth_token(token))


async def delete_user_token(session: AsyncSession, token: str) -> bool:
    """登出：把数据库里的 token 记录删掉（缓存由 clear_auth_cache 负责）"""
    result = await session.execute(delete(UserToken).where(UserToken.token == token))
    await session.commit()
    return result.rowcount > 0

async def update_user_info(update_data:UpdateUserInfo,session:AsyncSession,user_data:user):
    searched=await get_user_by_name(userReq=user_data,session=session)
    if not searched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="没找到该用户'")
    stmt=update(user).where(user.username==user_data.username).values(**update_data.model_dump(exclude_none=True,exclude_unset=True))
    result=await session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="没找到该用户2'")
    await session.commit()
    await session.refresh(searched)
    updated_user=await get_user_by_name(userReq=user_data,session=session)
    return updated_user


async def update_user_password(password_data:PasswordUpdate,session:AsyncSession,user:user):
    if not verify_password(password_data.old_password,user.password):
        return False
    hashed_password=get_hash_password(password_data.new_password)
    user.password=hashed_password
    await session.commit()
    await session.refresh(user)
    return True
