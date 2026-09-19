import json
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.ai_config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from models.ai import AIChat


async def stream_chat(message: str, history: list[dict] | None = None):
    """流式调用 AI。history 是之前的多轮对话（形如 [{"role":..., "content":...}]）"""
    messages = [{"role": "system", "content": "你是一个乐于助人的中文助手，回答要简洁。"}]

    # ★ 把历史对话拼进去（这样 AI 才能"记得"上文）
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": message})

    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}"
    }

    async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
        async with client.stream("POST", f"{AI_BASE_URL}/chat/completions", json=payload, headers=headers) as response:
            response.raise_for_status()
            async for chunk in response.aiter_lines():
                if not chunk.startswith("data: "):
                    continue
                text = chunk[6:]
                if text == "[DONE]":
                    break
                data = json.loads(text)
                notnull_data = data["choices"][0]["delta"].get("content", "")
                if notnull_data:
                    safe = notnull_data.replace("\r\n", "\n").replace("\n", "\ndata:")
                    yield safe


async def save_chat(session: AsyncSession, user_id: int, message: str, response: str):
    """存一轮对话（流结束后调用）"""
    record = AIChat(user_id=user_id, message=message, response=response)
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record


async def get_recent_chats(session: AsyncSession, user_id: int, limit: int = 10):
    """取最近 N 轮对话（按时间正序返回，便于拼成上下文）"""
    stmt = (
        select(AIChat)
        .where(AIChat.user_id == user_id)
        .order_by(AIChat.id.desc())          # 先按 id 倒序取"最新的 N 条"
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return list(reversed(rows))              # 再反转成"从旧到新"


async def get_history_for_ai(session: AsyncSession, user_id: int, limit: int = 10) -> list[dict]:
    """把最近的对话拼成 OpenAI 兼容的 messages 格式，发给 AI 用"""
    chats = await get_recent_chats(session, user_id, limit)
    messages = []
    for c in chats:
        messages.append({"role": "user", "content": c.message})
        messages.append({"role": "assistant", "content": c.response})
    return messages
        




    
     