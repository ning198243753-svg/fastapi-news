import asyncio
import httpx
from config.ai_config import AI_API_KEY, AI_BASE_URL, AI_MODEL

async def main():
    async with httpx.AsyncClient(timeout=60,trust_env=False) as client:
        response = await client.post(
            url=f'{AI_BASE_URL}/chat/completions',
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": AI_MODEL,
                "messages": [
                    {
                        "role": "system","content": "你好!"
                    }
                ],
                "stream": False
            }
        )
        print("状态码:", response.status_code)
        if response.status_code == 200:
            data=response.json()
            print("回答：",data["choices"][0]["message"]["content"][:60])
            print("花费:", data.get("usage", {}).get("credit"))
        else:
            print("错误信息:", response.text[:300])

asyncio.run(main())