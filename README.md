# 新闻资讯后端 API

基于 **FastAPI + MySQL + Redis** 的新闻资讯系统后端，提供用户认证、新闻浏览、收藏、浏览历史和 **AI 问答（流式输出）** 等能力。

配套前端：[xwzx-news](https://github.com/ning198243753-svg)（Vue 3 + Vant）

---

## 功能特性

| 模块 | 功能 |
|---|---|
| **用户** | 注册、登录、登出、查看/修改资料、修改密码 |
| **新闻** | 分类列表、分页列表、详情（含相关推荐、浏览量统计） |
| **收藏** | 收藏 / 取消收藏、收藏列表、检查收藏状态、清空 |
| **浏览历史** | 自动记录、历史列表、删除单条、清空 |
| **AI 问答** | 流式对话（SSE 打字机效果）、多轮上下文、历史记录 |

### 技术亮点

- **Redis 缓存**：分类（1 天）、列表（2 分钟）、详情（10 分钟）、**认证信息（10 分钟 + 主动失效）**
  - 认证缓存让每个需登录的请求从 **2 条 SQL 降为 0 条**
- **Redis 限流**：基于 `INCR` 原子操作的固定窗口限流，防止接口被刷
  - AI 问答：每用户 10 次/60 秒
  - 用户登录：每 IP 10 次/60 秒（防暴力猜密码）
- **流式响应**：调用 AI 服务后逐块转发给前端，实现打字机效果
- **多轮对话**：从数据库读取最近 N 轮历史拼进 prompt，AI 能记住上下文
- **统一异常处理**：业务异常、数据库异常、校验异常统一响应格式
- **健康检查**：`/health` 接口会真实探测 MySQL 和 Redis，依赖异常时返回 503
- **应用生命周期管理**：用 `lifespan` 在启动时自检、关闭时释放连接池
- **连接池健壮性**：`pool_recycle` + `pool_pre_ping`，避免 MySQL 空闲断连导致的随机报错

---

## 技术栈

| 分类 | 技术 |
|---|---|
| Web 框架 | FastAPI 0.141 |
| ASGI 服务器 | Uvicorn |
| ORM | SQLAlchemy 2.0（async） |
| 数据库 | MySQL 8.0（驱动：aiomysql） |
| 缓存 / 限流 | Redis 8（redis-py async） |
| 密码哈希 | passlib + bcrypt |
| HTTP 客户端 | httpx（异步，用于调用 AI 服务） |
| 配置管理 | python-dotenv |

---

## 项目结构

```
fastapi/
├── main.py                    # 应用入口：注册路由、中间件、异常处理
├── schema.sql                 # 建表脚本（8 张表）
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量示例（复制成 .env 使用）
│
├── config/                    # 配置
│   ├── db_config.py           # 数据库引擎 + get_session 依赖
│   ├── redis_config.py        # Redis 连接池 + get_redis 依赖
│   └── ai_config.py           # AI 服务配置（从 .env 读取）
│
├── models/                    # ORM 模型（SQLAlchemy）
│   ├── base.py                # 统一的 Base + 时间戳 Mixin
│   ├── users.py               # user / user_token
│   ├── news.py                # news / news_category
│   ├── favorite.py            # favorite
│   ├── history.py             # history
│   └── ai.py                  # ai_chat
│
├── schemas/                   # Pydantic 模型（请求/响应结构）
├── crud/                      # 业务数据层：查库、写库、调外部服务
├── routers/                   # 路由层：HTTP 参数解析、鉴权、响应
└── utils/
    ├── authenticate.py        # get_current_user 依赖（带认证缓存）
    ├── cache.py               # Redis 缓存工具（key 规范、序列化）
    ├── ratelimit.py           # 限流工具
    ├── security.py            # 密码哈希 / 校验
    ├── exception.py           # 各类异常处理器
    └── reseponse.py           # 统一响应格式
```

### 分层约定

```
routers/  →  处理 HTTP：解析参数、鉴权、包装响应
crud/     →  处理业务：查库、写库、调用外部服务（不感知 HTTP）
models/   →  数据库表结构
schemas/  →  接口的请求/响应契约
```

> `crud/` 里的函数**不写 `Depends`** —— 它由路由层调用，只接收普通参数。这是本项目踩过的坑之一。

---

## 快速开始

### 1. 环境要求

- Python 3.12+
- MySQL 8.0+
- Redis 6+

### 2. 建数据库

```bash
mysql -u root -p < schema.sql
```

> 脚本会创建 `news_app` 库、8 张表和 8 条新闻分类初始数据。
> 脚本是**幂等**的，可以重复执行。
>
> ⚠️ Windows 下用 `mysql.exe` 执行时，脚本开头的 `SET NAMES utf8mb4;` 不能删，否则中文会乱码。

### 3. 启动 Redis

```bash
# Ubuntu / Debian（WSL 同样适用）
sudo apt install redis-server
sudo service redis-server start
redis-cli ping          # 期望输出 PONG
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的数据库密码和 AI 服务的 API Key
```

### 5. 安装依赖并启动

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload
```

启动后打开接口文档：**http://127.0.0.1:8000/docs**

---

## 环境变量说明

| 变量 | 说明 | 示例 |
|---|---|---|
| `DEBUG` | 是否在错误响应里返回详细堆栈（**生产必须 false**） | `false` |
| `DATABASE_URL` | 数据库连接串 | `mysql+aiomysql://root:pwd@localhost:3306/news_app?charset=utf8mb4` |
| `DB_ECHO` | 是否打印 SQL 日志 | `true` / `false` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `AI_API_KEY` | AI 服务密钥 | `sk-xxxx` |
| `AI_BASE_URL` | AI 服务地址（OpenAI 兼容） | `https://xxx/v1` |
| `AI_MODEL` | 模型名 | `deepseek-v4.1-flash` |
| `AI_RATE_LIMIT` | AI 限流：窗口内最多次数 | `10` |
| `AI_RATE_WINDOW` | AI 限流：窗口秒数 | `60` |
| `AI_HISTORY_LIMIT` | 携带的历史轮数 | `10` |

> 任何 **OpenAI 兼容**的 AI 服务都能用（阿里云百炼、DeepSeek、各类中转站），只需改上面 3 个 AI 变量。

> ⚠️ **`DEBUG=true` 时，500 响应会带上完整 traceback（含文件路径、SQL 语句）**。
> 这只适合开发环境，**上线必须设为 `false`**。

---

## 接口一览

### 系统

| 方法 | 路径 | 说明 | 需要登录 |
|---|---|---|---|
| GET | `/health` | 健康检查（探测 MySQL + Redis，异常时返回 503） | ❌ |

### 用户

| 方法 | 路径 | 说明 | 需要登录 |
|---|---|---|---|
| POST | `/api/user/register` | 注册 | ❌ |
| POST | `/api/user/login` | 登录（返回 token） | ❌ |
| POST | `/api/user/logout` | 登出（删 token + 清缓存） | ❌ |
| GET | `/api/user/info` | 当前用户信息 | ✅ |
| PUT | `/api/user/update` | 修改资料 | ✅ |
| PUT | `/api/user/password` | 修改密码 | ✅ |

### 新闻

| 方法 | 路径 | 说明 | 需要登录 |
|---|---|---|---|
| GET | `/api/news/categories` | 分类列表（**有缓存**） | ❌ |
| GET | `/api/news/list?categoryId=1&page=1&pageSize=10` | 新闻列表（**有缓存**） | ❌ |
| GET | `/api/news/detail?id=1` | 详情 + 相关推荐（**内容有缓存，浏览量不缓存**） | ❌ |

### 收藏

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/favorite/check?newsId=1` | 是否已收藏 |
| POST | `/api/favorite/add` | 添加收藏（body: `{"newsId":1}`） |
| DELETE | `/api/favorite/remove?newsId=1` | 取消收藏 |
| GET | `/api/favorite/list?page=1` | 收藏列表 |
| DELETE | `/api/favorite/clear` | 清空收藏 |

### 浏览历史

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/history/add` | 记录浏览（body: `{"newsId":1}`） |
| GET | `/api/history/list?page=1` | 历史列表 |
| DELETE | `/api/history/delete/{history_id}` | 删除单条 |
| DELETE | `/api/history/clear` | 清空历史 |

### AI 问答

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/ai/chat` | 流式对话（SSE），**有登录 + 限流保护** |
| GET | `/api/ai/history?limit=20` | 历史对话记录 |

**鉴权方式**：请求头 `Authorization: <token>`（token 从登录接口获取）。

---

## AI 流式对话说明

请求：

```bash
curl -N -X POST http://127.0.0.1:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: <你的token>" \
  -d '{"message":"介绍一下 FastAPI"}'
```

响应（**SSE 格式，逐块到达**）：

```
data: FastAPI

data: 是一个

data: 现代

data: 高性能的

data: Web 框架

```

前端解析要点：

- 后端返回的是**纯文字**（不是 AI 服务的原始 JSON），格式为 `data: 内容\n\n`
- 用 `fetch` + `ReadableStream` 读取（`EventSource` 不支持 POST 和自定义请求头）
- 按 `\n\n` 切分消息，最后一段可能不完整，需要缓存到下一轮

---

## 缓存设计

| 数据 | Key | TTL | 失效方式 |
|---|---|---|---|
| 分类 | `news:categories:{skip}:{limit}` | 1 天 | TTL 自然过期 |
| 列表 | `news:list:cat:{id}:page:{p}:size:{s}` | 2 分钟 | TTL 自然过期 |
| 详情 | `news:detail:{id}` | 10 分钟 | TTL（**浏览量不缓存**） |
| 认证 | `auth:token:{token}` | 10 分钟 | **改资料 / 改密码 / 登出时主动删除** |
| 限流 | `ratelimit:ai_chat:{user_id}:{窗口号}` | 窗口长度 | TTL 自然过期 |

**设计要点**：

1. **缓存的 value 与直接返回的数据必须是同一份** —— 否则会出现"第一次请求字段名是 A、第二次是 B"的诡异问题
2. **会变的数据不缓存**：新闻详情里的浏览量每次实时查询
3. **敏感数据必须主动失效**：认证缓存不能只靠 TTL，否则用户登出后旧 token 仍可用
4. **Redis 的 `DEL` 不支持通配符** —— 按前缀批量删除要用 `SCAN` 逐个收集

---

## 开发注意事项（踩坑记录）

| 坑 | 说明 |
|---|---|
| **`Depends` 只能写在路由层** | 写在 `crud/` 里会得到 `'Depends' object has no attribute 'xxx'` |
| **流式响应的 session 会提前关闭** | `Depends(get_session)` 在流开始前就 commit/close 了，流结束后存库必须**新开 session** |
| **`Result.first()` 会关闭结果集** | 同一个 `result` 连续取值会报 `ResourceClosedError`，要先存变量 |
| **`.env` 改动不会触发 `--reload`** | uvicorn 只监听 `.py`，改 `.env` 要重启服务（或加 `--reload-include="*.env"`） |
| **外键表名是单数** | `ForeignKey("user.id")` 而不是 `users.id` |
| **所有模型要共享同一个 `Base`** | 否则跨表外键无法解析（`NoReferencedTableError`） |
| **有 `alias` 就要配 `populate_by_name`** | 否则用字段名传参会报 `Field required` |
| **MySQL 会断开空闲连接** | 默认 8 小时，必须配 `pool_recycle` + `pool_pre_ping`，否则服务跑几小时后随机报 `Lost connection` |
| **`DEBUG=true` 会泄露内部信息** | 500 响应里会带 traceback（文件路径、SQL），上线必须关 |
| **CORS 错误只出现在浏览器** | curl 能通、前端报错时，第一反应就该是 CORS |
| **WSL 重启后 Redis 不会自启** | 需要手动 `sudo service redis-server start`，或在 `/etc/wsl.conf` 配 `[boot] command` |

---

## 后续计划

- [x] ~~登录接口加限流（防暴力破解）~~
- [x] ~~健康检查 `/health`~~
- [x] ~~`lifespan` 管理应用生命周期~~
- [x] ~~连接池 `pool_recycle` + `pool_pre_ping`~~
- [ ] 接入 Alembic 管理数据库迁移
- [ ] 补充接口测试（pytest + httpx）
- [ ] 接入 CORS 白名单（目前是 `*`，仅适合本地开发）
- [ ] 用 `response_model` 声明响应契约
- [ ] 浏览量改为 Redis 计数 + 定时批量回写
- [ ] 结构化日志 + 请求 ID
- [ ] Docker 一键部署
- [ ] CI（GitHub Actions：跑测试 + lint）

---

## 工程化参考

本项目目前是一个**功能完整的学习项目**，已具备：分层清晰、缓存设计、流式接口、统一异常、健康检查、限流。

**与生产级项目的主要差距**：

| 维度 | 现状 | 生产级需要 |
|---|---|---|
| 数据库迁移 | 手写 `schema.sql` | Alembic（可追溯、可回滚） |
| 测试 | 无 | pytest（核心接口集成测试） |
| 接口契约 | 手写 dict 返回 | `response_model` 声明 |
| 日志 | SQL echo + print | 结构化日志 + 请求 ID + 集中收集 |
| 监控 | 无 | Prometheus + 告警 |
| 错误上报 | 手写异常处理 | Sentry |
| CORS | `*`（仅本地开发） | 白名单 |
| 部署 | 手动 uvicorn | Docker + CI/CD |
| 权限 | 仅登录/未登录 | RBAC |

**建议改造顺序**：

1. 安全收尾：CORS 白名单、确认 `DEBUG=false`
2. 规范：`pydantic-settings` 统一配置、`response_model`、Alembic
3. 质量：pytest + ruff + 结构化日志
4. 工程化：Docker + GitHub Actions CI
5. 进阶：监控、链路追踪、幂等性、RBAC

---

## License

仅供学习交流使用。
