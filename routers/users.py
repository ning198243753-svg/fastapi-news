from starlette import status
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from redis import Redis
from config.db_config import get_session
from config.redis_config import get_redis
from crud import users
from models.users import user
from schemas.users import PasswordUpdate, UpdateUserInfo, UserDataResponse, UserInfoResponse, UserRequest
from sqlalchemy.ext.asyncio import AsyncSession

from utils.authenticate import get_current_user
from utils.ratelimit import check_rate_limit
from utils.reseponse import sucess_response

router = APIRouter(prefix="/api/user", tags=["users"])

# 登录/注册的限流参数（防暴力猜密码 / 批量注册）
LOGIN_RATE_LIMIT = 10        # 每窗口最多 10 次
LOGIN_RATE_WINDOW = 60       # 窗口 60 秒


def _client_ip(request: Request) -> str:
    """取客户端 IP（登录限流按 IP 计数）

    注意：如果前面有 Nginx 等反向代理，要读 X-Forwarded-For。
    开发环境直接用 request.client.host 就行。
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register")
async def register_user(userReq: UserRequest, session: AsyncSession = Depends(get_session)):
    exsiting_user = await users.get_user_by_name(session, userReq)
    if exsiting_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user_data = await users.user_register(session, userReq)
    token = await users.create_user_token(session, user_data.id)
    response_entity = UserDataResponse(token=token,userInfo=(UserInfoResponse.model_validate(user_data)))
    response = sucess_response(response_entity,message="注册成功")
    return response

@router.post("/login")
async def user_login(
    user_data: UserRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    # ★ 限流：按「客户端 IP」计数，防暴力猜密码
    await check_rate_limit(
        redis, "user_login", _client_ip(request), LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW
    )

    user = await users.authenticate_user(user_data, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="用户名或者密码错误")
    token = await users.create_user_token(session,userid=user.id)
    response_entity = UserDataResponse(token=token,userInfo=UserInfoResponse.model_validate(user))
    response = sucess_response(response_entity,message="登陆成功")
    return response

@router.get("/info")
async def user_info(user:user=Depends(get_current_user)):
    return sucess_response(UserInfoResponse.model_validate(user),message="获取信息成功")

@router.put("/update")
async def user_update(
    update_data:UpdateUserInfo,
    session:AsyncSession=Depends(get_session),
    redis:Redis=Depends(get_redis),
    user:user=Depends(get_current_user),
    authorization:str=Header(...,alias="Authorization"),
):
    result=await users.update_user_info(update_data=update_data,session=session,user_data=user)
    # 资料改了 → 删掉认证缓存，否则最长 10 分钟里拿到的还是旧资料
    await users.clear_auth_cache(redis, authorization.replace("Bearer ",""))
    return sucess_response(UpdateUserInfo.model_validate(result),message="更新成功")

@router.put("/password")
async def password_update(
    new_password:PasswordUpdate,
    session:AsyncSession=Depends(get_session),
    redis:Redis=Depends(get_redis),
    user:user=Depends(get_current_user),
    authorization:str=Header(...,alias="Authorization"),
):
    # 改密码需要真正的 ORM 对象（要写 user.password + refresh），所以从库里重新取
    db_user = await users.get_user_orm_by_id(session, user.id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not await users.update_user_password(new_password, session, db_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="修改失败")
    # 密码改了 → 删掉认证缓存（安全：避免旧缓存让旧 token 继续可用）
    await users.clear_auth_cache(redis, authorization.replace("Bearer ",""))
    return sucess_response(message="修改成功")

@router.post("/logout")
async def user_logout(
    session:AsyncSession=Depends(get_session),
    redis:Redis=Depends(get_redis),
    authorization:str=Header(...,alias="Authorization"),
):
    """登出：同时删掉「Redis 缓存」和「数据库里的 token 记录」

    注意：这里不用 get_current_user，因为即使 token 已失效也要能成功登出（幂等）。
    """
    token = authorization.replace("Bearer ","")
    await users.clear_auth_cache(redis, token)      # 删缓存
    await users.delete_user_token(session, token)   # 删数据库里的 token
    return sucess_response(message="已退出登录")


