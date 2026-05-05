# 回声 - 后端服务

> 深夜情绪急救站 — AI 陪伴后端服务

---

## 项目简介

回声是一个面向年轻人的情绪陪伴应用，提供 AI 对话、情绪日记、树洞吐槽、动态广场等功能。后端采用 FastAPI 构建，提供 RESTful API 和 WebSocket 实时通信支持。

---

## 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 框架 | FastAPI | 高性能异步 API 框架 |
| 数据库 | SQLite / MySQL | SQLAlchemy ORM，支持异步操作 |
| 缓存 | Redis | 会话存储、短期记忆、限流 |
| AI | OpenAI API | GPT-4o-mini 模型 |
| 认证 | JWT | RS256 非对称签名 |
| 部署 | Docker | Docker Compose 编排 |

---

## 项目结构

```
backend/
├── app/
│   ├── core/           # 核心配置、错误处理、响应封装
│   ├── enums/          # 枚举定义
│   ├── middleware/      # 中间件（认证、请求上下文）
│   ├── models/         # SQLAlchemy 模型
│   ├── prompts/        # AI 对话提示词模板
│   ├── routers/        # API 路由
│   │   ├── ai.py       # AI 对话接口
│   │   ├── auth.py     # 认证接口
│   │   ├── diaries.py  # 日记接口
│   │   ├── treehole.py # 树洞接口
│   │   ├── posts.py    # 动态接口
│   │   ├── notifications.py  # 通知接口
│   │   ├── stats.py    # 统计接口
│   │   └── users.py    # 用户接口
│   ├── schemas/        # Pydantic 请求/响应模型
│   └── services/       # 业务逻辑服务
│       ├── auth_service.py      # 认证服务
│       ├── chat_service.py      # AI 对话服务
│       ├── connection_manager.py # WebSocket 管理
│       ├── social_level.py      # 社交等级服务
│       └── storage.py            # 文件存储服务
├── alembic/            # 数据库迁移
├── tests/              # 测试文件
├── config/             # 配置文件
├── main.py             # 应用入口
├── Dockerfile
└── pyproject.toml
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Redis（可选，用于生产环境）
- MySQL（可选，SQLite 用于开发）

### 1. 安装依赖

```bash
cd backend
pip install -e .
```

### 2. 配置环境变量

```bash
cp ../.env.example .env
# 编辑 .env 文件，填入必要的配置
```

主要配置项：

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `DATABASE_URL` | 数据库连接 URL | 是 |
| `REDIS_URL` | Redis 连接 URL | 否（开发环境） |
| `JWT_SECRET` | JWT 密钥 | 是 |
| `OPENAI_API_KEY` | OpenAI API Key | 是 |
| `ALLOWED_ORIGINS` | CORS 允许的源 | 是 |

### 3. 初始化数据库

```bash
# 创建迁移
alembic revision --autogenerate -m "init"

# 执行迁移
alembic upgrade head
```

### 4. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Docker
docker-compose up -d
```

---

## API 文档

启动服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 主要功能模块

### 1. AI 对话

- **路由**: `POST /api/v1/ai/chat` - 发送消息获取 AI 回复
- **路由**: `GET /api/v1/ai/personality` - 获取 AI 性格列表
- **路由**: `WebSocket /ws/chat/{user_id}` - 实时对话
- **特性**: 支持 SSE 流式输出、短期记忆、危机干预

### 2. 认证

- **路由**: `POST /api/v1/auth/login` - 登录
- **路由**: `POST /api/v1/auth/register` - 注册
- **路由**: `POST /api/v1/auth/sms/send` - 发送验证码
- **路由**: `POST /api/v1/auth/refresh` - 刷新 Token

### 3. 情绪日记

- **路由**: `GET /api/v1/diaries` - 获取日记列表
- **路由**: `POST /api/v1/diaries` - 创建日记
- **路由**: `GET /api/v1/diaries/weekly-report` - 获取周报

### 4. 树洞

- **路由**: `GET /api/v1/treehole/posts` - 获取树洞列表
- **路由**: `POST /api/v1/treehole/posts` - 发布树洞
- **路由**: `POST /api/v1/treehole/posts/{id}/resonate` - 共鸣

### 5. 动态广场

- **路由**: `GET /api/v1/posts` - 获取动态列表
- **路由**: `POST /api/v1/posts` - 发布动态
- **路由**: `POST /api/v1/posts/{id}/like` - 点赞

---

## 数据模型

### 用户 (User)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| phone | String | 手机号 |
| nickname | String | 昵称 |
| avatar_url | String | 头像 URL |
| ai_personality | Enum | 当前 AI 性格 |
| is_minor | Boolean | 是否未成年 |
| social_level | Integer | 社交等级 |

### AI 消息 (AIMessage)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户 ID |
| conversation_id | UUID | 对话 ID |
| role | Enum | user/assistant |
| content | Text | 消息内容 |
| crisis_detected | Boolean | 是否检测到危机 |

### 日记 (Diary)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户 ID |
| content | Text | 日记内容 |
| emotion_tone | Enum | 情绪色调 |
| record_date | Date | 记录日期 |

---

## 安全机制

### JWT 认证

- 使用 RS256 非对称签名
- Access Token 有效期 2 小时
- Refresh Token 有效期 7 天

### 危机干预

- AI 回复自动检测危机关键词
- 检测到危机时触发干预流程
- 提供专业帮助资源和热线

### 未成年人保护

- 强制青少年模式
- 内容过滤
- 使用时长限制

---

## 开发指南

### 添加新的 API 路由

1. 在 `app/routers/` 下创建或编辑路由文件
2. 定义 Pydantic Schema
3. 在 `app/main.py` 中注册路由

```python
# app/routers/example.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/example", tags=["示例"])

@router.get("/items")
async def list_items():
    return {"items": []}
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "description"

# 更新到最新
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 运行测试

```bash
pytest tests/ -v
```

---

## 部署

### Docker Compose

```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 环境变量

生产环境需要设置以下环境变量：

```bash
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/echo
REDIS_URL=redis://host:6379/0
JWT_SECRET=your-production-secret
OPENAI_API_KEY=your-api-key
```

---

## 相关文档

- [产品需求文档](../PRD.md)
- [技术架构文档](../tech_architecture.md)
- [前端技术方案](../frontend_tech.md)
- [UI 设计规范](../ui_design.md)
- [统一 UI 指南](../UNIFIED_UI_GUIDE.md)
