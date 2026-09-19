import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from config.ai_config import AI_HISTORY_LIMIT, AI_RATE_LIMIT, AI_RATE_WINDOW
from config.db_config import async_session, get_session
from config.redis_config import get_redis
from crud import ai
from models.users import user
from schemas.ai import ChatRequest
from utils.authenticate import get_current_user
from utils.ratelimit import check_rate_limit
from utils.reseponse import sucess_response

logger = logging.getLogger(__name__)

router=APIRouter(prefix="/api/ai",tags=["ai"])

# 拼给 AI 的历史轮数、限流参数 —— 都从 .env 读（见 config/ai_config.py）

@router.post("/chat")
async def chat(
    message:ChatRequest,
    session:AsyncSession=Depends(get_session),
    redis:Redis=Depends(get_redis),
    user:user=Depends(get_current_user),      # ← 要登录（AI 调用要花钱，必须防刷）
):
    # ⓿ 限流：每个用户每 AI_RATE_WINDOW 秒最多 AI_RATE_LIMIT 次（超了直接 429）
    await check_rate_limit(redis, "ai_chat", str(user.id), AI_RATE_LIMIT, AI_RATE_WINDOW)

    # ① 流开始之前：从数据库取历史（此时 session 还有效）
    history = await ai.get_history_for_ai(session, user.id, AI_HISTORY_LIMIT)
    user_id = user.id                        # 先把需要的值取出来，避免后面用到已关闭的 session
    user_message = message.message

    async def generator():
        full = []                            # 收集完整回答（流结束后要存库）
        try:
            async for chunk in ai.stream_chat(user_message, history):
                full.append(chunk)
                yield f"data: {chunk}\n\n"
        finally:
            # ② 流结束后存库
            # ⚠️ 不能用在参数里注入的那个 session —— 它已经随着请求结束而关闭了，
            #    所以这里自己开一个新的 session
            if full:
                try:
                    async with async_session() as s:
                        await ai.save_chat(s, user_id, user_message, "".join(full))
                        await s.commit()
                except Exception:
                    logger.exception("保存 AI 对话失败（不影响已返回的内容）")

    return StreamingResponse(generator(),media_type="text/event-stream")


@router.get("/history")
async def get_ai_history(
    session:AsyncSession=Depends(get_session),
    user:user=Depends(get_current_user),
    limit:int=Query(20,ge=1,le=100),
):
    """取当前用户的历史对话（按时间正序，展开成一问一答交错的列表）"""
    chats = await ai.get_recent_chats(session, user.id, limit)

    data = []
    for c in chats:
        created = c.created_at.isoformat() if c.created_at else None
        data.append({"role": "user", "content": c.message, "createdAt": created})
        data.append({"role": "assistant", "content": c.response, "createdAt": created})

    return sucess_response(data=data, message="查询成功")


    