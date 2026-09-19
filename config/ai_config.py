import os

from dotenv import load_dotenv

load_dotenv()

AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("AI_MODEL")

# 限流参数：每 AI_RATE_WINDOW 秒最多 AI_RATE_LIMIT 次
# 注意：.env 里读出来都是【字符串】，必须转成 int
AI_RATE_LIMIT = int(os.getenv("AI_RATE_LIMIT", "10"))       # 不写就用默认值 10
AI_RATE_WINDOW = int(os.getenv("AI_RATE_WINDOW", "60"))     # 默认 60 秒

# 拼给 AI 的历史轮数（防止越聊越贵 / 超上下文上限）
AI_HISTORY_LIMIT = int(os.getenv("AI_HISTORY_LIMIT", "10"))
