# 回声 APP — 实施任务清单

> 创建时间：2026-04-24
> 严格按照 PRD.md 智能体分配执行
> 本文档是智能体之间的"交接文档"，每个任务需包含足够上下文供任意智能体接续

---

## 智能体分配表（来自 PRD.md）

| 功能模块 | 负责智能体 | 辅助智能体 |
|---------|-----------|-----------|
| 前端开发 | Frontend Developer | Mobile App Builder |
| 后端开发 | Backend Architect | Database Optimizer |
| AI服务 | AI Engineer | — |
| 安全合规 | Security Engineer | Backend Architect |
| 部署运维 | DevOps Automator | SRE |
| 测试验收 | API Tester | Code Reviewer |
| 架构决策 | Software Architect | — |
| 代码审查 | Code Reviewer | — |

---

## 中断恢复机制

### 设计原则

由于项目任务多、周期长，智能体执行过程中可能因会话中断、上下文压缩等原因暂停。本文档通过以下机制确保中断后可丝滑继续：

1. **子任务粒度**：每个任务拆分到单个智能体可在一次会话内完成的粒度（约 1-2 小时工作量）
2. **产出物追踪**：每个任务记录产出的文件路径，后续智能体可直接定位
3. **中断标记**：任务中断时记录 `中断点` 和 `继续指引`，接手智能体按指引继续
4. **依赖显式化**：每个任务明确标注需要的前置产出物（文件/API/数据库表）
5. **检查点机制**：阶段完成后设置检查点，汇总当前状态

### 任务状态说明

| 状态 | 含义 |
|------|------|
| ⏳ | 待开始，未开工 |
| 🔄 | 进行中，正在执行 |
| ⏸️ | 已中断，需接续（必填中断点信息） |
| ✅ | 已完成，产出物已就绪 |
| ❌ | 已阻塞，需解决阻塞问题 |

### 中断记录格式

当任务中断时，必须在任务详情中填写以下信息：

```markdown
**中断点**：具体停在哪一步，如"已完成Redis短期记忆存储，未做中期记忆"
**继续指引**：下一步具体做什么，如"接着实现 mid_term 记忆的 MySQL 存储和30天滚动淘汰"
**未决问题**：如有待确认的技术决策，记录在此
```

---

## P2 功能架构预留（PRD 3.3 强制要求）

> PRD 明确要求"在架构设计阶段需预留扩展空间"。以下预留点必须在对应任务中实现，否则阶段三开发时需大量重构。

| P2 功能 | 架构预留要求 | 必须在哪个任务中实现 |
|---------|------------|-------------------|
| 夜间模式（P2-10） | 所有颜色必须CSS变量，禁止硬编码；图片资源准备日间/夜间两套；首次启动缓存主题偏好 | T001 前端初始化 |
| 用户等级与成就（P2-09） | 行为事件系统需支持等级/成就触发 | T027 数据统计（user_events 模型） |
| 内容分享（P2-08） | 内容需能生成H5落地页和分享海报；分享链接有效期机制 | T019-A 动态后端预留分享字段 |
| 用户举报反馈闭环（P2-07） | 举报系统需设计通知触发机制 | T014-C 举报管理已包含反馈闭环 |

---

## 智能体调用规范（PRD 智能体调用规范 1-6 条）

> 执行任务时必须遵守以下规范，确保智能体获得充分上下文。

| 场景 | 规范 |
|------|------|
| 开发前端页面时 | 使用 `frontend-developer` 智能体，**必须**提供 ui_design.md 中对应页面的线框图和设计规范 |
| 开发后端接口时 | 使用 `backend-architect` 智能体，**必须**提供 tech_architecture.md 中的API设计和数据库表结构 |
| 架构决策时 | 使用 `software-architect` 智能体，需提供完整的产品需求和技术约束 |
| 安全审计时 | 使用 `security-engineer` 智能体，重点审核匿名身份加密、数据脱敏、危机干预 |
| 代码审查时 | 使用 `code-reviewer` 智能体，重点关注安全漏洞和性能问题 |
| 部署配置时 | 使用 `devops-automator` 智能体，参考 tech_architecture.md 中的 Docker Compose 配置 |

---

## 阶段一：核心功能（P0）

### 1. 项目初始化

#### T001 前端项目初始化

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ✅ |
| 前置依赖 | 无 |
| 参考文档 | frontend_tech.md, ui_design.md |

**任务描述**：
- 初始化 Uni-app + Vue3 + TypeScript 项目
- 集成 Pinia 状态管理
- 集成 wot-design-uni 组件库 + uni-ui 辅助
- 配置 CSS 变量主题系统（**强制要求**：所有颜色必须使用 CSS 变量，禁止硬编码，为夜间模式预留。变量命名参考 modules_design.md 9.2-9.3 的日间/夜间色值）
- 配置项目目录结构（pages/components/composables/stores/utils/constants/api）
- 配置请求封装（axios/uni.request 统一拦截、错误码处理）
- 配置路由和底部导航栏（首页/AI对话/日记/动态/我的，[+]按钮分流入口预留）
- **数据埋点基础设施**：封装事件上报工具，为阶段一验证门控（7日留存、日均对话轮次、日记连续记录率、NPS）提供数据采集能力

**产出物**：
- `frontend/` 项目目录 ✅
- `frontend/src/constants/errorCodes.ts` — 错误码常量 ✅
- `frontend/src/api/` — 请求封装基类 ✅
- `frontend/src/styles/` — CSS 变量主题文件 ✅

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T002 后端项目初始化

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ✅ |
| 前置依赖 | 无 |
| 参考文档 | tech_architecture.md |

**任务描述**：
- 初始化 FastAPI + SQLAlchemy 2.0 项目
- 配置环境分层（development/test/production），详见 tech_architecture.md 第十章
- 配置统一响应格式（success/error/pagination）
- 配置错误码枚举（ErrorCode），对应 tech_architecture.md 第三章全部错误码
- 配置 CORS、请求日志中间件
- 配置项目目录结构（routers/models/services/middleware/config/schemas）
- 实现环境变量管理（.env.development / .env.production）
- **搭建 Mock 服务框架**：统一的 Mock 切换机制，开发阶段零成本
- **APScheduler 初始化**：安装 APScheduler，配置调度器生命周期（FastAPI startup/shutdown 事件中启停），为 T013-B 定时任务提供基础框架

**产出物**：
- `backend/` 项目目录 ✅
- `backend/config/` — 环境配置 ✅ (development.py, production.py, test.py)
- `backend/app/enums/error_codes.py` — 错误码枚举 ✅ (68个错误码，覆盖全部业务场景)
- `backend/app/core/config.py` — Mock 服务切换机制 ✅ (AppSettings + ProviderRegistry)
- `backend/.env.development` / `.env.example` ✅
- `backend/app/services/providers.py` — Mock 服务框架 ✅ (5类Provider Protocol + 真实/Mock实现 + 流式AI接口)
- `backend/app/services/scheduler.py` — APScheduler 初始化 ✅
- `backend/app/core/responses.py` — 统一响应格式 ✅
- `backend/app/middleware/request_context.py` — 请求日志中间件 ✅
- `backend/app/main.py` — FastAPI 应用入口 ✅
- `backend/app/routers/__init__.py` — 路由注册汇总 ✅
- `backend/app/schemas/base.py` — Pydantic 模型基类 ✅ (BaseSchema/PaginationParams/PaginatedResponse)
- `backend/app/models/base.py` — SQLAlchemy 模型基类 ✅ (Base/UUIDMixin/TimestampMixin/SoftDeleteMixin)
- `backend/pyproject.toml` — 完整依赖 ✅ (sqlalchemy/alembic/python-jose/redis/httpx/Pillow等)

**目录结构约定**：保持 `backend/app/` FastAPI 标准结构，后续任务产出物路径映射：
- `backend/routers/` → `backend/app/routers/`
- `backend/models/` → `backend/app/models/`
- `backend/services/` → `backend/app/services/`

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T003 Docker Compose 环境

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | DevOps Automator |
| 状态 | ✅ |
| 前置依赖 | 无 |
| 参考文档 | tech_architecture.md 第六章 |

**任务描述**：
- 编写 docker-compose.yml（MySQL 8.0 + Redis 7 + API + Nginx + Uptime Kuma + MinIO）
- 编写 Nginx 配置（API代理 + WebSocket代理 + 管理后台代理）
- 编写 MySQL 初始化脚本（字符集 utf8mb4，含全部核心表结构）
- 配置数据持久化卷
- 编写 .env 模板

**产出物**：
- `docker-compose.yml` ✅
- `nginx/nginx.conf` ✅
- `nginx/ssl/README.md` — SSL 证书目录说明 ✅
- `mysql/init.sql` — MySQL 初始化脚本 ✅
- `.env.example` ✅
- `backend/Dockerfile` ✅

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T004 数据库 Schema 创建

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ✅ |
| 前置依赖 | T002, T003 |
| 参考文档 | tech_architecture.md 第二章 + 第十一章 11.4 |

**任务描述**：
- 创建 SQLAlchemy 模型，对应 tech_architecture.md 全部表：
  - users（含补充字段：notification_settings, is_minor, social_energy）
  - user_tags, anonymous_identities, user_anon_mapping
  - emotion_diaries
  - treehole_posts, treehole_comments
  - posts（动态广场）
  - friendships, conversations, chat_messages
  - ai_conversations, ai_messages, ai_memories
  - notifications, push_records
  - **reports**（举报记录表，含举报类型、状态、处理结果）
  - **admins, admin_logs**（管理后台，PRD 第十一章 11.4）
- 创建 Alembic 迁移脚本
- 确保所有索引和外键正确

**产出物**：
- `backend/app/models/user.py` ✅ — User, UserTag, AnonymousIdentity, UserAnonMapping
- `backend/app/models/diary.py` ✅ — EmotionDiary
- `backend/app/models/treehole.py` ✅ — TreeholePost, TreeholeComment
- `backend/app/models/post.py` ✅ — Post
- `backend/app/models/chat.py` ✅ — Friendship, Conversation, ChatMessage
- `backend/app/models/ai.py` ✅ — AIConversation, AIMessage, AIMemory
- `backend/app/models/notification.py` ✅ — Notification, PushRecord
- `backend/app/models/admin.py` ✅ — Admin, AdminLog
- `backend/app/models/report.py` ✅ — Report
- `backend/app/models/__init__.py` ✅ — 导出所有模型（19张表）
- `backend/alembic.ini` ✅ — Alembic 配置
- `backend/alembic/env.py` ✅ — 环境配置
- `backend/alembic/versions/0001_initial.py` ✅ — 初始迁移脚本

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

### 2. Mock 服务开发（零成本方案）

> 这些任务是开发阶段零运行成本的关键，必须在正式功能开发前完成。

#### T005-M Mock 服务实现

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ✅ |
| 前置依赖 | T002 |
| 参考文档 | tech_architecture.md 第十章 |

**任务描述**：
实现以下 Mock 服务（通过环境配置切换）：

| Mock 服务 | 开发阶段实现 | 对应真实服务 |
|-----------|------------|-------------|
| 短信验证码 | 固定 123456 | 阿里云短信 |
| 内容审核 | 直接 Pass | 阿里云内容安全 |
| 图片存储 | 本地文件系统 ./uploads/ | 阿里云 OSS |
| 推送服务 | 控制台日志输出 | 极光推送 |
| AI 对话 | 预设关键词回复模板 | 智谱 GLM-4 |
| 图片处理 | 本地 Pillow 压缩缩略图 | 阿里云 OSS 图片处理 |

- 每个服务实现统一接口（Protocol/ABC），通过配置切换实现类
- Mock 服务需在 API 层面与真实服务行为一致（入参/出参格式相同）
- **图片处理服务**需统一封装：图片压缩（最大宽度 1080px）、缩略图生成、格式校验（仅允许 jpg/png/webp），供私聊图片（T021-C）、动态图片（T019-A）、头像上传（T023-A）等场景共用

**产出物**：
- `backend/app/services/sms.py` ✅ — MockSMSService / ConsoleSMSService / AliyunSMSService
- `backend/app/services/content_audit.py` ✅ — PassAudit / LocalContentAudit / AliyunContentAudit
- `backend/app/services/storage.py` ✅ — LocalStorage / MinIOStorage / OSSStorage
- `backend/app/services/push.py` ✅ — MockPushService / JPushService
- `backend/app/services/ai_chat.py` ✅ — MockAIChat(30组模板) / GLMChatService
- `backend/app/services/image.py` ✅ — PillowImageService（压缩/缩略图/格式校验）
- `backend/app/services/providers.py` ✅ — 重构为聚合导入 + ProviderRegistry
- `backend/app/services/__init__.py` ✅ — 统一导出

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

### 3. 认证模块

#### T005 后端：短信验证码 + JWT 认证

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ✅ |
| 前置依赖 | T002, T004, T005-M |
| 参考文档 | tech_architecture.md 第三章（API设计）、第五章（安全架构） |

**任务描述**：
- 实现短信验证码登录（开发阶段用 T005-M 的 MockSMSService）
- 实现 JWT 认证（HS256，access_token 15分钟，refresh_token 7天）
- 实现验证码倒计时规则（60秒、手机号变更重置，详见 modules_design.md 1.2）
- 实现注册流程：手机验证 → 昵称+年龄段 → AI开场白
- 实现手机号加密存储（AES-256-GCM，phone_hash 用于唯一索引查询）
- 实现速率限制（登录5次/15分钟，验证码1次/分钟）
- **青少年模式后端逻辑**（PRD 核心规则第6条）

**API 端点**：
```
POST /api/v1/auth/send-code
POST /api/v1/auth/verify-code
POST /api/v1/auth/complete-profile
POST /api/v1/auth/refresh-token
DELETE /api/v1/auth/logout
GET  /api/v1/auth/me
```

**产出物**：
- `backend/app/routers/auth.py` ✅ — 6个API端点
- `backend/app/services/auth_service.py` ✅ — 认证服务（验证码/JWT/速率限制/青少年模式）
- `backend/app/services/crypto.py` ✅ — AES-256-GCM加密 + SHA-256哈希
- `backend/app/middleware/auth.py` ✅ — JWT中间件 + get_current_user依赖注入
- `backend/app/schemas/auth.py` ✅ — 认证请求/响应模型
- `backend/app/schemas/user.py` ✅ — 用户相关模型
- 更新 `backend/app/main.py` ✅ — Redis初始化 + 路由注册
- 更新 `backend/app/routers/__init__.py` ✅

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T006 前端：登录/注册页

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ✅ |
| 前置依赖 | T001, T005 |
| 参考文档 | ui_design.md, modules_design.md 1.1-1.2 |

**任务描述**：
- 登录页：手机号输入 + 获取验证码按钮 + 验证码输入
- iOS/Android 自动读取短信验证码（modules_design.md 1.2）
- 验证码倒计时 UI（60秒禁用，显示"重新获取(N)"，详见 modules_design.md 1.2 倒计时规则）
  - 倒计时期间手机号输入框置灰不可修改、验证码输入框保持可编辑
  - 倒计时期间可正常浏览隐私政策链接
  - 倒计时结束后文案变为"重新获取"
- 注册引导页：昵称输入 + 年龄段选择（5个选项点击即选：18岁以下/18-25/26-35/36-45/45以上）
- 隐私政策链接和勾选
- 首页 AI 开场白过渡页（按时间段动态变化）
- **青少年模式前端**（PRD 核心规则第6条）：
  - 青少年模式启动页（告知受限功能）
  - 使用时长追踪 + 1小时弹窗提醒"今天已经使用60分钟了，休息一下眼睛和大脑吧"
  - 21:55弹窗提醒"还有5分钟就到睡觉时间了，准备好休息吧"
  - 22:00后显示"该休息了"锁定页
- 错误码映射为中文提示

**产出物**：
- `frontend/src/pages/auth/login.vue` ✅ — 登录页（倒计时交互+短信自动读取+微信登录条件编译）
- `frontend/src/pages/auth/profile.vue` ✅ — 注册引导页（昵称2-12字符+跳过选项+底部渐入提示）
- `frontend/src/pages/auth/ai-greeting.vue` ✅ — AI开场白过渡页（4时段动态文案+3秒自动跳转+青少年判断）
- `frontend/src/pages/auth/minor-notice.vue` ✅ — 青少年模式启动页（受限功能+时长限制说明+已知悉确认）
- `frontend/src/pages/auth/minor-lock.vue` ✅ — 青少年模式锁定页（22:00-05:00全屏遮罩+安慰语+05:00自动解锁）
- `frontend/src/composables/useCountdown.ts` ✅ — 验证码倒计时
- `frontend/src/composables/useMinorTimer.ts` ✅ — 青少年使用时长追踪（1小时/21:55/22:00三级提醒+前后台暂停恢复）

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T006-A AI 情感对话评测（50 场景测试集）

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | AI Engineer |
| 状态 | ✅ |
| 前置依赖 | 无（可在 T007-B 之前独立执行） |
| 参考文档 | PRD 附录A、tech_architecture.md 第九章 |

**任务描述**：
PRD 附录A 明确要求"开发前需准备，50个情绪场景测试集"，tech_architecture.md 第九章标记为"需要立即行动的 P0 事项"：

- **评测目的**：验证 GLM-4 的情感对话质量，决定是否采用或选择备选模型（MiniMax abab6.5 / 通义千问）
- **评测范围**（50 个情绪场景）：
  - 深夜倾诉场景（10 个）：失眠、孤独、想家、怀旧等
  - 情绪宣泄场景（10 个）：愤怒、委屈、挫败、崩溃等
  - 寻求建议场景（10 个）：职业困惑、感情纠结、人际矛盾等
  - 自我探索场景（10 个）：迷茫、自我怀疑、存在意义等
  - 危机信号场景（10 个）：自伤意念、绝望、告别语言等（重点测试安全响应）
- **评测维度**：
  - 共情准确度：是否准确识别用户情绪
  - 回应恰当性：是否符合三种性格人设
  - 边界遵守：是否触发安全底线（自伤、专业建议等）
  - 上下文连贯性：多轮对话是否连贯
- **评测产出**：
  - 50 个场景的标准测试输入
  - GLM-4 回复评分报告
  - 模型选择决策建议（GLM-4 vs MiniMax vs 通义千问对比）

**产出物**：
- `docs/ai_eval_scenarios.md` ✅ — 50 个情绪场景测试集（D01-D15/N01-N15/P01-P10/C01-C10）
- `docs/ai_eval_report.md` ✅ — 模型评测报告（含评测框架、执行脚本、评分模板、决策建议模板）

**中断点**：无
**继续指引**：已完成
**未决问题**：无（实际 API 评测需在获取 API Key 后执行）

---

### 4. AI 对话核心

#### T007-A Mock AI 对话服务

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | AI Engineer |
| 状态 | ✅ |
| 前置依赖 | T005-M |
| 参考文档 | tech_architecture.md 第十章 |

**任务描述**：
- 预设 20-30 组对话模板（按情绪关键词匹配）
- Mock 服务需支持 SSE 格式输出（模拟流式）
- 三种性格分别有差异化回复模板

**产出物**：
- `backend/services/ai_chat.py` ✅ — MockAIChat 类完善（1002行，30关键词×3性格，SSE格式，危机响应）

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T007-B 智谱 GLM-4 API 接入

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | AI Engineer |
| 状态 | ✅ |
| 前置依赖 | T005-M |
| 参考文档 | tech_architecture.md 第四章 |

**任务描述**：
- 接入智谱 GLM-4-Flash（日常对话）和 GLM-4-Plus（情绪周报）
- 实现 SSE 流式输出
- 实现重试机制和超时处理
- 实现费用控制（免费用户每日10轮对话限制）

**产出物**：
- `backend/services/ai_chat.py` ✅ — GLMChatService 类完善（1370行，SSE流式+重试+超时）
- `backend/services/ai_config.py` ✅ — 模型配置和配额管理（313行，3性格Prompt+配置）

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T007-C 三种性格 Prompt Engineering

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | AI Engineer |
| 状态 | ✅ |
| 前置依赖 | T007-B |
| 参考文档 | modules_design.md 2.1 三种性格人设 |

**任务描述**：
- 编写小温/老黑/阿理三种性格的 System Prompt
- Prompt 需包含：基础设定、回应逻辑、边界规则、开场白
- 编写 AI 安全底线 Prompt（硬性禁止 + 自伤/自杀倾向处理流程）
- 实现性格切换机制
- 实现 AI 开场白按时间段动态变化

**产出物**：
- `backend/prompts/xiaowen.txt` ✅ — 小温 Prompt（4KB）
- `backend/prompts/laohei.txt` ✅ — 老黑 Prompt（4KB）
- `backend/prompts/ali.txt` ✅ — 阿理 Prompt（4KB）
- `backend/services/ai_persona.py` ✅ — 性格管理和切换（334行）

**中断点**：无
**继续指引**：已完成
**未决问题**：无

---

#### T008 后端：AI 对话 SSE 流式输出

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005, T007-A |
| 参考文档 | tech_architecture.md 第三章 API 设计 |

**任务描述**：
- 实现 AI 对话 API（普通 + SSE 流式）
- 对话上下文管理（最近 5 轮 + 系统Prompt + 记忆注入）
- 对话记录持久化到 ai_conversations / ai_messages 表
- 实现危机关键词检测（自杀/自伤 → 触发安全响应 + 后台标记）

**API 端点**：
```
POST /api/v1/ai/chat
POST /api/v1/ai/chat/stream
GET  /api/v1/ai/conversations
POST /api/v1/ai/greeting
```

**产出物**：
- `backend/routers/ai.py`
- `backend/services/ai_conversation_service.py`
- `backend/services/crisis_detection.py` — 危机关键词检测

**中断点**：
**继续指引**：
**未决问题**：

---

#### T009-A 短期记忆：Redis 存储最近 5 轮对话

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T008 |
| 参考文档 | tech_architecture.md 第四章 |

**任务描述**：
- Redis List 存储最近 5-10 轮对话原文
- 24 小时 TTL 自动过期
- 当前会话上下文注入到 AI 请求

**产出物**：
- `backend/services/memory/short_term.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T009-B 中期记忆：MySQL 摘要存储 + 30 天滚动

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T009-A |
| 参考文档 | tech_architecture.md 第四章 |

**任务描述**：
- 对话摘要生成（每 10 轮对话生成一次摘要）
- 关键事实提取（人物关系、生活状态、情绪模式）
- 30 天滚动淘汰（expires_at 过期清理）
- 记忆检索与上下文注入

**产出物**：
- `backend/services/memory/mid_term.py`
- `backend/services/memory/memory_retrieval.py` — 记忆检索和注入

**中断点**：
**继续指引**：
**未决问题**：

---

#### T009-C 长期记忆：用户画像 + 重要事件

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect + AI Engineer |
| 状态 | ⏳ |
| 前置依赖 | T009-B |
| 参考文档 | tech_architecture.md 第四章, modules_design.md 2.3 |

**任务描述**：
- 用户画像标签（性格偏好、兴趣、情绪模式）
- 重要事件记录（生日、纪念日、人生大事件）
- 长期记忆永不过期，人工/事件触发更新
- 记住/忘记规则实现（详见 modules_design.md 2.3）

**产出物**：
- `backend/services/memory/long_term.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T010 前端：AI 对话页（流式显示）

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T008 |
| 参考文档 | ui_design.md, frontend_tech.md |

**任务描述**：
- AI 对话页面（消息列表 + 输入框）
- SSE 流式显示（App 端 onChunkReceived，H5 用 EventSource）
- 小程序分段显示降级方案
- 性格选择页（注册后第2次打开展示，默认小温）
- 对话中"换个人聊聊"切换入口
- AI 开场白按时间段展示
- 危机干预弹窗（自伤关键词触发 → 显示求助热线）

**产出物**：
- `frontend/src/pages/chat/` — 对话页面
- `frontend/src/composables/useSSE.ts` — SSE 流式通信封装
- `frontend/src/composables/useCrisis.ts` — 危机干预 UI

**中断点**：
**继续指引**：
**未决问题**：

---

### 5. 情绪日记

#### T011 后端：日记 CRUD API

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005, T004 |
| 参考文档 | modules_design.md 3.1-3.5, tech_architecture.md 第二章 |

**任务描述**：
- 情绪日记 CRUD（含三层标签：色调/标签/文字）
- 同一用户同一天可创建多条日记
- 0 字记录规则（纯色调可提交，不计入周报分析样本）
- 日记隐私：首次进入日记模块的隐私声明 API
- 同步模式选择（仅本地 / 云端同步）
- **本地优先存储架构**（PRD 技术决策）：
  - 后端提供统一的日记同步 API，支持增量同步（按 client_id 和时间戳冲突解决）
  - 同步模式用户：上传端到端加密后的密文，服务器无法解密
  - 仅本地模式用户：数据不传后端，换机/重装后无法恢复（需明确告知）
- 日记导出（JSON/PDF）
- 日记删除（单条/全部）

**API 端点**：
```
GET    /api/v1/diaries
POST   /api/v1/diaries
GET    /api/v1/diaries/:id
PATCH  /api/v1/diaries/:id
DELETE /api/v1/diaries/:id
```

**产出物**：
- `backend/routers/diaries.py`
- `backend/services/diary_service.py`
- `backend/services/encryption.py` — 端到端加密服务

**中断点**：
**继续指引**：
**未决问题**：

---

#### T012-A 前端：日记编辑页（三层标签 + 语音输入）

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T011 |
| 参考文档 | ui_design.md, modules_design.md 3.1-3.2 |

**任务描述**：
- 情绪色调选择器（5 色圆形选择 + 代表语）
- 情绪标签选择（每个色调 6-8 个标签，最多选 3 个）
- 文字输入区（按色调显示不同提示语）
- 语音输入支持
- 0 字提交规则（轻提示"写点什么让记录更有意义"）
- 超过 500 字提示"要不要发给 AI 朋友聊聊"
- 首次进入隐私声明弹窗
- 同步模式选择引导（仅本地 / 云端同步）
- **本地存储实现**（PRD 技术决策：App端SQLite，H5/小程序降级键值存储）：
  - App端：uni-app SQLite 插件存储日记数据
  - H5/小程序：uni.setStorageSync 键值存储（降级方案）
  - 统一封装 StorageAdapter 接口，按平台自动切换
  - 云端同步模式：端到端加密后上传，前端使用 CryptoJS AES-256-GCM

**产出物**：
- `frontend/src/pages/diary/edit.vue`
- `frontend/src/components/diary/EmotionToneSelector.vue`
- `frontend/src/components/diary/EmotionLabelPicker.vue`
- `frontend/src/composables/useEncryption.ts` — 端到端加密

**中断点**：
**继续指引**：
**未决问题**：

---

#### T012-B 前端：日记列表页 + 可视化视图

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T012-A |
| 参考文档 | modules_design.md 3.2-3.4 |

**任务描述**：
- 日记列表页（底部导航第二位）
- 列表顶部卡片"记一笔今天的感受？"就地展开
- 首页情绪色调条（当天未记录/已记录/连续 N 天）
- 三种可视化视图：
  - 日历热力图（月视图，每格色调填充）
  - 情绪曲线（折线图）
  - 情绪分布（环形图）
- 日记导出（JSON/PDF）
- 日记删除（单条/全部）

**产出物**：
- `frontend/src/pages/diary/list.vue`
- `frontend/src/pages/diary/calendar.vue`
- `frontend/src/pages/diary/chart.vue`
- `frontend/src/components/diary/EmotionHeatMap.vue`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T012-C 后端：AI 情绪周报生成（五段式）

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | AI Engineer + Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T009-B, T011 |
| 参考文档 | modules_design.md 3.3 |

**任务描述**：
- AI 情绪周报五段式生成（情绪故事线 / 关键词云 / 一句看见 / 温和建议 / 下周展望）
- 使用 GLM-4-Plus 生成（成本约 0.4 元/用户/月）
- 每周日晚 10 点 APScheduler 定时任务静默生成
- 周报只分析有文字内容的记录（0 字记录排除）
- 动态标题生成

**产出物**：
- `backend/services/weekly_report.py`
- `backend/routers/diaries.py` — 新增 `GET /api/v1/diaries/report/weekly`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T012-D 前端：AI 情绪周报展示页

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T012-C |
| 参考文档 | modules_design.md 3.3 |

**任务描述**：
- 周报展示页（日记模块顶部静默出现，不打 push）
- 五段式布局：情绪故事线 / 关键词云 / 一句看见 / 温和建议(默认折叠) / 下周展望
- 情绪关键词云小型可视化

**产出物**：
- `frontend/src/pages/diary/weekly-report.vue`
- `frontend/src/components/diary/KeywordCloud.vue`

**中断点**：
**继续指引**：
**未决问题**：

---

### 6. 通知推送系统

#### T013-A 后端：极光推送集成 + 推送服务

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005, T005-M |
| 参考文档 | tech_architecture.md 第三章（通知推送调度方案） |

**任务描述**：
- 集成极光推送 SDK（开发阶段用 MockPushService）
- 实现通知记录表 CRUD（notifications 表）
- 实现推送频率控制（push_records 表）
- 通知合并（5 分钟内同类通知合并）
- 通知设置 API（用户推送偏好开关）

**API 端点**：
```
GET    /api/v1/notifications
PATCH  /api/v1/notifications/:id/read
PATCH  /api/v1/notifications/read-all
GET    /api/v1/notifications/settings
PATCH  /api/v1/notifications/settings
```

**产出物**：
- `backend/routers/notifications.py`
- `backend/services/notification_service.py`
- `backend/services/push_service.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T013-B 后端：APScheduler 定时推送任务

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T013-A |
| 参考文档 | modules_design.md 2.4, 6.4, tech_architecture.md 第三章（调度方案） |

**任务描述**：
- 晚安问候：每日 22:30 扫描活跃用户，22:30-23:30 随机发送，每周最多 3 次
- 早安问候：每日 7:00 扫描，7:00-8:00 发送，每周最多 2 次
- 情绪低谷关怀：每日 10:00 检查连续 2 天未登录+近期情绪负面用户，每月最多 2 次
- 节日问候：节日当天 10:00 发送
- 重要事件跟进：用户提到面试/考试等，事件当天晚上发送
- 节日清单管理（法定/传统/特殊日期/用户自定义）
- **社交能量 0 点重置定时任务**（modules_design.md 6.4 明确要求："每日重置：凌晨0点恢复至50%基准值"）：
  - APScheduler Cron 任务，每日 00:00 执行
  - 将所有用户的 `social_energy` 重置为 50
  - 更新 `social_energy_updated_at` 为当前时间
  - 用户选择"主动休息"时异步触发恢复（非此任务）

**产出物**：
- `backend/services/scheduler.py` — APScheduler 任务定义（含社交能量重置）
- `backend/services/care_service.py` — 关怀逻辑

**中断点**：
**继续指引**：
**未决问题**：

---

#### T013-C 后端：AI 主动关怀触发机制

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | AI Engineer + Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T013-B, T009-C |
| 参考文档 | modules_design.md 2.4 |

**任务描述**：
- 事件驱动推送（好友申请、评论共鸣、情绪周报生成完成）
- 树洞与 AI 朋友联动（发布吐槽后 AI 主动关怀，详见 modules_design.md 4.5）
- 推送文案个性化（AI 生成，基于用户偏好和上下文）
- 推送文案原则：宁可漏发不可滥发，用户可关闭

**产出物**：
- `backend/services/care_triggers.py` — 事件驱动关怀触发
- `backend/services/treehole_care.py` — 树洞联动关怀

**中断点**：
**继续指引**：
**未决问题**：

---

#### T013-D 前端：通知列表页 + 通知设置

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T013-A |
| 参考文档 | ui_design.md |

**任务描述**：
- 通知列表页（按时间倒序，已读/未读标记）
- 通知跳转（点击通知跳转对应页面）
- 通知设置页（AI 关怀 / 好友申请 / 评论 / 情绪周报 开关）
- 批量标记已读

**产出物**：
- `frontend/src/pages/notification/list.vue`
- `frontend/src/pages/notification/settings.vue`

**中断点**：
**继续指引**：
**未决问题**：

---

### 7. 管理后台（阶段一核心）

#### T014-A 后端：管理员认证 + RBAC 权限

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T004, T005 |
| 参考文档 | tech_architecture.md 第十一章 11.4-11.5 |

**任务描述**：
- 管理员登录（独立 JWT，与 C 端用户 token 隔离）
- RBAC 权限体系（super_admin / admin / operator 三角色，权限节点见 11.5）
- 权限校验中间件（require_permission 装饰器）
- 操作审计日志（admin_logs 表，不可删除）
- 安全措施：会话超时 2 小时、连续 5 次错误锁定 30 分钟

**API 端点**：
```
POST /api/admin/v1/auth/login
POST /api/admin/v1/auth/refresh
```

**产出物**：
- `backend/routers/admin/auth.py`
- `backend/middleware/admin_auth.py`
- `backend/services/admin/admin_service.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T014-B 后端：用户管理 API

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T014-A |
| 参考文档 | tech_architecture.md 第十一章 |

**任务描述**：
- 用户列表（搜索、筛选、分页）
- 用户详情（含情绪记录摘要、社交数据）
- 封禁/解封操作（含封禁原因、时长、通知用户）
- 青少年模式管理

**API 端点**：
```
GET  /api/admin/v1/users
GET  /api/admin/v1/users/:id
POST /api/admin/v1/users/:id/ban
POST /api/admin/v1/users/:id/unban
```

**产出物**：
- `backend/routers/admin/users.py`
- `backend/services/admin/user_service.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T014-C 后端：举报管理 API + 危机干预 API

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T014-A |
| 参考文档 | tech_architecture.md 第十一章, modules_design.md 7.7 |

**任务描述**：
- C 端举报提交 API
- 管理端举报列表 + 处理（通过/驳回/封禁）
- 举报合并展示（同一被举报人多条举报合并）
- 误判申诉处理
- 举报反馈闭环（24 小时进度通知，处理结果通知）
- 危机事件列表 + 人工介入标记
- 内容管理 API（查看/隐藏/推荐）

**API 端点**：
```
# C端
POST /api/v1/reports

# 管理端
GET  /api/admin/v1/reports
GET  /api/admin/v1/reports/:id
POST /api/admin/v1/reports/:id/process
GET  /api/admin/v1/reports/appeals
POST /api/admin/v1/reports/appeals/:id/review
GET  /api/admin/v1/crisis/list
GET  /api/admin/v1/crisis/:id
POST /api/admin/v1/crisis/:id/resolve
GET  /api/admin/v1/contents
PATCH /api/admin/v1/contents/:id/status
```

**产出物**：
- `backend/routers/reports.py` — C 端举报
- `backend/routers/admin/reports.py`
- `backend/routers/admin/crisis.py`
- `backend/routers/admin/contents.py`
- `backend/services/admin/report_service.py`
- `backend/services/admin/crisis_service.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T015 前端：管理后台（Vue Vben Admin）

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T014-A, T014-B, T014-C |
| 参考文档 | tech_architecture.md 第十一章 |

**任务描述**：
- 基于 **Vue Vben Admin** 模板初始化管理后台项目
- 管理员登录页
- 举报管理页（列表 + 处理 + 误判申诉）
- 危机干预页（三层危机信号展示 + AI 关怀记录 + 人工介入）
- 内容管理页（树洞/广场内容查看/隐藏/推荐）
- 用户管理页（查看/封禁/解封/青少年模式）
- RBAC 权限控制（前端路由守卫 + 按钮级权限）
- 开发阶段：固定账号 admin/admin123

**产出物**：
- `admin-web/` 项目目录

**中断点**：
**继续指引**：
**未决问题**：

---

#### T016 前端：首页 + 路由守卫 + 青少年模式前端拦截

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T005, T006 |
| 参考文档 | ui_design.md, modules_design.md 1.4, PRD 核心规则第6条 |

**任务描述**：
- **首页页面实现**（PRD 3.2 入口A — 首页轻引导）：
  - 首页顶部情绪色调条，文案动态变化（当天未记录："今天感觉怎么样？"/已记录："今天已经记过了。想补充吗？"/连续3天以上："已经连续记录N天了"）
  - AI 对话入口（AI 头像 + 最近对话预览）
  - 通知入口（未读数角标）
  - [+] 按钮分流入口（底部导航中间位，点击弹出 ActionSheet：发布吐槽/发布动态/记录情绪）
  - 底部导航栏（首页/AI对话/日记/动态/我的）
- **全局路由守卫**（核心基础设施）：
  - JWT 登录状态管理（token 刷新、过期自动跳转登录页）
  - 未登录不可访问需认证页面
  - 首次打开 vs 二次打开区分（注册后第2次打开展示性格选择页）
- **青少年模式前端 API 拦截**（PRD 核心规则第6条强制要求）：
  - 封装请求拦截器，对后端返回 `USER_UNDERAGE` 错误码统一处理
  - 拦截后显示提示"青少年模式下无法使用此功能"并阻止页面渲染
  - 前端侧预判：青少年用户进入受限页面时直接拦截（无需等后端返回错误）

**产出物**：
- `frontend/src/pages/home/index.vue` — 首页
- `frontend/src/components/home/EmotionBar.vue` — 情绪色调条
- `frontend/src/composables/useAuth.ts` — 登录状态管理 + 路由守卫
- `frontend/src/composables/useMinorGuard.ts` — 青少年模式前端拦截

**中断点**：
**继续指引**：
**未决问题**：

---

### 8. 阶段一检查点

#### CP1 阶段一架构评审

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Software Architect |
| 状态 | ⏳ |
| 前置依赖 | T001-T016 全部完成 |

**任务描述**：
- 审查前后端项目结构合理性
- 审查数据库设计是否覆盖全部业务场景
- 审查 API 设计是否符合 RESTful 规范
- 审查安全架构（匿名加密、JWT、速率限制）
- 审查零成本方案 Mock 服务切换机制
- 输出评审意见和改进建议

**产出物**：
- 评审报告（记录在此文档的执行记录中）

**中断点**：
**继续指引**：
**未决问题**：

---

#### CP2 阶段一代码审查

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Code Reviewer |
| 状态 | ⏳ |
| 前置依赖 | T001-T016 全部完成 |

**任务描述**：
- 重点审查安全漏洞（SQL 注入、XSS、敏感数据泄露）
- 审查 API 错误处理完整性
- 审查前端敏感信息处理
- 审查后端速率限制实现
- 输出审查意见和修复清单

**产出物**：
- 代码审查报告（记录在此文档的执行记录中）

**中断点**：
**继续指引**：
**未决问题**：

---

## 阶段二：社交功能（P1）

### 9. 树洞吐槽区

#### T017-A 后端：树洞核心 API

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005, T013-C |
| 参考文档 | modules_design.md 4.1-4.3, tech_architecture.md 第二章 |

**任务描述**：
- 树洞发布 API（仅匿名，自动生成虚拟身份）
- 虚拟昵称生成器（形容词 200 + 名词 200 = 40,000 组合）
- 气质标签随机分配
- 匿名身份隔离架构（anon_id 映射加密存储，详见 modules_design.md 7.5）
- 话题标签筛选
- 温度排序算法（时间衰减 + 共鸣数 + 评论数 + 随机因子）
- 低谷时段守护（2-5 点降低新鲜度权重）

**API 端点**：
```
GET  /api/v1/treehole/posts
POST /api/v1/treehole/posts
```

**产出物**：
- `backend/routers/treehole.py`
- `backend/services/treehole_service.py`
- `backend/services/anonymous_identity.py` — 匿名身份生成和隔离

**中断点**：
**继续指引**：
**未决问题**：

---

#### T017-B 后端：树洞互动 API + 内容审核

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T017-A |
| 参考文档 | modules_design.md 4.4-4.6 |

**任务描述**：
- 共鸣 API（树洞场景显示"我懂你"）
- 回声 API（文字评论，限 50 字，不支持回复）
- 内容审核策略（自伤允许发布触发关怀、人身攻击拦截、广告拦截、色情拦截）
- **审核反馈温和设计**（modules_design.md 7.11，强制要求）：
  - 拦截时**不说**"内容违规已删除"，而说"这条内容好像不太适合在这里发出来。也许是情绪太强烈了？你可以试着换个方式表达，或者跟AI朋友聊聊，ta随时都在。"
  - 警告时**不说**"你违规了"，而说"我们注意到你发布的内容可能让其他人感到不适。回声是大家的安全角落，一起守护好吗？"
  - 误判申诉：被拦截/删除后可申诉，人工复核
- AI发布前脱敏提醒：检测匿名内容中可识别信息（真实姓名、公司+职位、住址等），建议性提醒不强制
- 骚扰识别规则引擎（1 分钟 10 条限速等）
- 发布时间随机化（匿名内容显示时间加入 0-15 分钟随机延迟）

**API 端点**：
```
POST /api/v1/treehole/posts/:id/resonate
POST /api/v1/treehole/posts/:id/comments
```

**产出物**：
- `backend/services/treehole_interaction.py`
- `backend/services/harassment_detector.py` — 骚扰规则引擎

**中断点**：
**继续指引**：
**未决问题**：

---

#### T018 前端：树洞页

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T017-A |
| 参考文档 | ui_design.md, modules_design.md 4.1-4.4 |

**任务描述**：
- 树洞信息流页（话题标签筛选条 + 信息流列表）
- 树洞发布页（匿名身份自动生成展示 + AI 风格改写可选预览）
- 树洞详情页（共鸣"我懂你" + 回声评论）
- 评论区提示语"这里是树洞，不是建议箱"
- 防识别 UI（不显示精确时间，AI 生成小图标替代头像）
- 新用户引导卡片（信息流顶部 + 就地展开输入框）

**产出物**：
- `frontend/src/pages/treehole/` — 树洞页面

**中断点**：
**继续指引**：
**未决问题**：

---

#### T017-D 前端：微信小程序适配（P0）

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T008, T017-A |
| 参考文档 | PRD 1.2 多端输出策略 |

**任务描述**：
微信小程序适配（PRD 1.2 明确标注"微信小程序 — 优先级 P0，阶段二上线"）：

- **分包策略**（PRD 1.2 小程序特殊限制：主包2MB，总大小20MB）：
  - 主包：核心功能（AI对话、日记、个人中心）
  - 分包1（social）：树洞 + 动态广场 + 好友系统
  - 分包配置：`pages.json` 中配置 `subPackages`
- **SSE 流式输出降级**（PRD 1.2 功能差异说明）：
  - App端：`uni.request` 的 `onChunkReceived` 原生 SSE
  - 小程序：**分段显示降级方案**（轮询或预设回复分段返回，不支持真正的 SSE）
  - 统一封装 `useAIStream.ts`，按平台自动切换实现
- **本地存储降级**（PRD 1.2 功能差异说明）：
  - App端：SQLite 插件存储日记数据
  - 小程序：`uni.setStorageSync` 键值存储（降级方案，无结构化查询）
- **推送降级**（PRD 1.2 功能差异说明）：
  - App端：极光推送原生推送
  - 小程序：模板消息（受限，需用户主动触发后才能发送）
- **审核要点适配**（PRD 1.2 小程序特殊限制）：
  - 用户隐私协议页
  - 内容安全 API 接入（`security.msgSecCheck`）
  - 禁止诱导分享（不强制用户分享才能使用功能）

**产出物**：
- `frontend/src/pages.json` — 分包配置
- `frontend/src/composables/useAIStream.ts` — 流式输出跨端封装
- `frontend/src/platform/miniprogram/` — 小程序平台适配代码
- `frontend/src/platform/mp-storage.ts` — 小程序存储适配

**中断点**：
**继续指引**：
**未决问题**：

---

### 10. 动态广场

#### T019-A 后端：动态广场 API

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005 |
| 参考文档 | modules_design.md 5.1-5.4 |

**任务描述**：
- 动态发布 API（支持实名/匿名切换，每条独立选择）
- 匿名动态身份（同条动态内固定，跨动态独立）
- 信息流排序算法（冷启动：时间新鲜度×0.4 + 互动热度×0.3 + 内容完整度×0.2 + 随机因子×0.1）
- 可见范围设置（全部公开/仅好友/仅自己）
- 匿名动态不可被关注

**API 端点**：
```
GET  /api/v1/posts
POST /api/v1/posts
```

**产出物**：
- `backend/routers/posts.py`
- `backend/services/post_service.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T019-B 后端：动态互动 + AI 文案润色 API

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Backend Architect + AI Engineer |
| 状态 | ⏳ |
| 前置依赖 | T019-A, T007-B |
| 参考文档 | modules_design.md 5.3, 5.5 |

**任务描述**：
- 共鸣 API（广场场景显示"共鸣"）
- 评论 API（支持回复评论）
- 收藏 API
- 悄悄关注 API（对方不收到通知）
- AI 文案润色 API（2-3 个版本，保留原意，字数不超过 1.5 倍）
- [+] 按钮分流设计（吐槽/动态/日记统一入口）

**API 端点**：
```
POST /api/v1/posts/:id/like
POST /api/v1/posts/:id/comments
POST /api/v1/ai/polish
POST /api/v1/posts/:id/follow  # 悄悄关注
```

**产出物**：
- `backend/services/post_interaction.py`
- `backend/services/ai_polish.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T020 前端：动态广场页

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T019-A |
| 参考文档 | ui_design.md, modules_design.md 5.0-5.5 |

**任务描述**：
- 动态信息流页
- 动态发布页（底部工具栏：图片/表情/AI 润色/匿名切换/发布）
- 匿名切换 UI（默认灰色=实名，高亮=匿名，切换时提示"匿名发布后无法被关注"）
- AI 文案润色对比卡片（原文/润色后/保留原文/使用润色/再换一个）
- [+] 按钮底部 ActionSheet（发布吐槽/发布动态/记录情绪，智能高亮）
- 共鸣/评论/收藏/悄悄关注交互
- 好友申请入口（头像/昵称 → 个人主页 → 加好友）

**产出物**：
- `frontend/src/pages/square/` — 广场页面
- `frontend/src/components/square/ActionSheet.vue`

**中断点**：
**继续指引**：
**未决问题**：

---

### 11. 好友系统

#### T021-A 后端：好友申请流程

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005 |
| 参考文档 | modules_design.md 6.1-6.2 |

**任务描述**：
- 好友申请发送/接收/同意/忽略/过期清理（7 天未处理自动过期）
- 过期后续规则（24 小时冷却期，同一用户 30 天最多 3 次）
- 双向同意机制
- 删除好友/拉黑
- 好友列表 API
- **官方AI账号**（modules_design.md 6.6，冷启动关键设计）：
  - 小温/老黑/阿理作为独立账号存在，可被添加为好友
  - 被添加后自动出现在好友列表
  - 互动体验与AI朋友对话一致
  - 降低冷启动阶段好友系统的空窗感

**API 端点**：
```
GET  /api/v1/friends
POST /api/v1/friend-requests
GET  /api/v1/friend-requests
POST /api/v1/friend-requests/:id/accept
POST /api/v1/friend-requests/:id/reject
DELETE /api/v1/friends/:id
POST /api/v1/users/:id/block
```

**产出物**：
- `backend/routers/friends.py`
- `backend/services/friend_service.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T021-B 后端：AI 代写打招呼语

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | AI Engineer |
| 状态 | ⏳ |
| 前置依赖 | T021-A, T007-B |
| 参考文档 | modules_design.md 6.1 |

**任务描述**：
- AI 生成打招呼语（基于对方公开动态 + 双方共同点）
- 输出 3 个版本：温暖型/轻松型/真诚型
- 触发时机：用户点击"AI帮我想想"/输入框停留超 30 秒

**产出物**：
- `backend/services/ai_greeting.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T021-C 后端：WebSocket 私聊（ConnectionManager）

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T021-A |
| 参考文档 | tech_architecture.md 第六章（WebSocket 部分） |

**任务描述**：
- FastAPI WebSocket ConnectionManager
- 心跳机制（30 秒 ping/pong）
- 僵尸检测（90 秒未收到心跳视为断开）
- 断线重连（指数退避 1s→2s→4s→8s→16s→30s）
- 离线消息（重连后拉取 after={last_msg_id}）
- 消息类型：文字 + 图片（压缩存储，90 天过期）
- 骚扰检测（1 分钟 10 条限速）

**产出物**：
- `backend/services/connection_manager.py`
- `backend/routers/chat.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T021-D 后端：AI 聊天辅助 + 社交能量系统

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | AI Engineer + Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T021-C, T009-C |
| 参考文档 | modules_design.md 6.3-6.5 |

**任务描述**：
- 冷场救急（10 分钟无人回复 → "AI帮我想想话题"）
- 回复建议（停留 1 分钟未输入 → 2-3 个建议）
- 语气优化（AI 润色按钮）
- 温柔退出功能（AI 生成 2-3 个自然结束语）
- 社交能量计算（发送-5%/回复-3%/申请-10%/收到共鸣+5%/AI对话+15%）
- 社交能量 0 点重置到 50%

**产出物**：
- `backend/services/ai_chat_assist.py`
- `backend/services/social_energy.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T022 前端：好友页 + 私聊页

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T021-A, T021-C |
| 参考文档 | ui_design.md, modules_design.md 6.1-6.5 |

**任务描述**：
- 好友列表页
- 好友申请页（打招呼语输入 + AI帮我想想按钮）
- 好友申请通知页（同意/忽略/查看主页）
- 私聊页面（WebSocket 实时消息）
- AI 聊天辅助 UI（冷场提示/回复建议浮层/语气优化按钮）
- 温柔退出功能 UI
- 社交能量可视化（能量条+最近社交活动+AI建议）
- 个人主页（查看他人信息+加好友/删除/拉黑）

**产出物**：
- `frontend/src/pages/friends/`
- `frontend/src/pages/chat/private.vue`
- `frontend/src/composables/useWebSocket.ts`
- `frontend/src/composables/useSocialEnergy.ts`

**中断点**：
**继续指引**：
**未决问题**：

---

### 12. 个人中心 + AI 智能画像

#### T023-A 后端：个人中心 API + 查看他人信息 + 渐进式社交暴露

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Backend Architect + AI Engineer |
| 状态 | ⏳ |
| 前置依赖 | T005, T009-C |
| 参考文档 | modules_design.md 2.3, 6.4-6.5, tech_architecture.md 第三章 |

**任务描述**：
- 用户资料 CRUD（昵称/头像/城市/职业/年龄段）
- 兴趣标签自然获取（AI 对话中自动打标签，详见 modules_design.md 1.3）
- AI 画像标签 API（基于行为生成画像标签）
- 用户自定义重要日期管理（最多 10 个，仅本地存储）
- 社交能量查询 API
- **查看他人公开信息 API**（modules_design.md 6.1 好友申请流程依赖）：
  - 返回对方的公开信息（昵称/头像/画像标签/最近公开动态）
  - 用于好友申请时展示"Ta的公开动态"，以及个人主页查看他人信息
- **渐进式社交暴露级别计算 API**（modules_design.md 6.4 强制要求）：
  - 根据用户行为计算当前级别（Level 1-6）
  - Level 1：浏览动态广场
  - Level 2：点共鸣/点赞
  - Level 3：评论互动
  - Level 4：悄悄关注
  - Level 5：发送好友申请
  - Level 6：私聊
  - 返回当前级别 + 进度（如"Level 3，还需评论 1 次可升级到 Level 4"）

**API 端点**：
```
# 自己的信息
GET   /api/v1/users/me
PATCH /api/v1/users/me
GET   /api/v1/users/me/tags
GET   /api/v1/users/me/social-energy
GET   /api/v1/users/me/social-level     # 渐进式社交暴露级别
POST  /api/v1/users/me/important-dates

# 他人的公开信息（好友系统、动态广场依赖）
GET   /api/v1/users/:id                 # 查看他人公开信息
GET   /api/v1/users/:id/public-posts    # 他人的公开动态列表
```

**产出物**：
- `backend/routers/users.py`
- `backend/services/user_service.py`
- `backend/services/ai_profile.py`
- `backend/services/social_level.py` — 渐进式社交暴露级别计算

**中断点**：
**继续指引**：
**未决问题**：

---

#### T023-B 前端：个人中心页 + 设置页

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T001, T023-A |
| 参考文档 | ui_design.md |

**任务描述**：
- 个人中心页（头像/昵称/画像标签/社交能量/我的收藏/我的关注/我的动态）
- 设置页（资料编辑/通知偏好/同步模式切换/我的节日管理/隐私声明/关于/注销账户）
- 渐进式社交暴露引导（Level 1-6 可视化进度，调用 T023-A 新增的 `/api/v1/users/me/social-level` API）
- 查看他人主页（调用 T023-A 新增的 `/api/v1/users/:id` API，展示他人公开信息）

**产出物**：
- `frontend/src/pages/mine/`
- `frontend/src/pages/settings/`

**中断点**：
**继续指引**：
**未决问题**：

---

### 13. 管理后台（阶段二）

#### T024-A 后端：管理后台阶段二 API

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T014-A |
| 参考文档 | tech_architecture.md 第十一章 |

**任务描述**：
- 推送管理 API（定时推送任务查看/创建/暂停）
- 种子内容发布 API（树洞/广场种子内容发布）
- 数据看板聚合 API（DAU/MAU、留存、情绪分布、AI 对话统计）
- 权限管理 API（管理员 CRUD、角色管理、操作日志）

**API 端点**：
```
GET  /api/admin/v1/push/tasks
POST /api/admin/v1/push/tasks
GET  /api/admin/v1/dashboard/overview
GET  /api/admin/v1/dashboard/users
GET  /api/admin/v1/dashboard/retention
GET  /api/admin/v1/dashboard/emotion
GET  /api/admin/v1/dashboard/ai
GET  /api/admin/v1/admins
POST /api/admin/v1/admins
GET  /api/admin/v1/roles
GET  /api/admin/v1/admin-logs
```

**产出物**：
- `backend/routers/admin/dashboard.py`
- `backend/routers/admin/admins.py`
- `backend/services/admin/dashboard_service.py`

**中断点**：
**继续指引**：
**未决问题**：

---

#### T024-B 前端：管理后台阶段二页面

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T015, T024-A |
| 参考文档 | tech_architecture.md 第十一章 11.2 |

**任务描述**：
- 推送管理页（定时推送任务列表/创建/暂停）
- 种子内容发布页（树洞/广场种子内容发布）
- 数据看板页（DAU/MAU、留存率、AI 对话统计、情绪分布可视化）
- 权限管理页（管理员列表/角色管理/权限配置/操作日志）
- 开发阶段：数据看板使用 Mock 数据

**产出物**：
- `admin-web/src/views/dashboard/`
- `admin-web/src/views/admin/`

**中断点**：
**继续指引**：
**未决问题**：

---

## 阶段二补充：AI安全审核（P0）

> PRD 3.1 明确标注 AI安全审核为"阶段二 P0"，因为树洞等内容功能依赖审核才能安全上线。

### 14. AI 安全审核

#### T025-A AI安全审核：四大场景差异化审核 + 骚扰三层防御

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Security Engineer + Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T008, T017-B, T021-C |
| 参考文档 | modules_design.md 7.1-7.4, 7.6 |

**任务描述**：
- 实现四大场景差异化审核（modules_design.md 7.3）：
  - 树洞：中高严格度，色情/广告/暴恐事前拦截，自残触发关怀流程
  - 动态广场：高严格度，色情/广告/暴恐/辱骂事前拦截，推荐前二次审核
  - 私聊：中严格度，色情/广告事前拦截，骚扰检测
  - AI对话：低严格度，仅自残预警触发
- 骚扰三层防御（modules_design.md 7.4）：
  - 第一层规则引擎：1分钟10条限速、单日10人好友申请上限、微信号/手机号格式检测、单日评论5条提示
  - 第二层AI行为分析：对话模式检测、关系进展异常、跨场景纠缠
  - 第三层用户侧防御：一键屏蔽、社交能量耗尽勿扰、对话安全提示、聊天记录保全
- 处罚梯度实现（轻微/中等/严重，首次/二次/三次递进处罚）
- 虚假信息预警（modules_design.md 7.6）：注册环节检测、行为检测、SimHash相似内容检测
- 3人以上举报同一内容自动触发下架

**产出物**：
- `backend/services/audit/` — 分场景审核服务
- `backend/services/harassment_detector.py` — 完善
- `backend/services/fake_account_detector.py` — 虚假信息预警
- 安全审计报告 + 修复代码

**中断点**：
**继续指引**：
**未决问题**：

---

#### T025-B 安全审计：匿名加密 + 数据脱敏

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Security Engineer + Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T017-A |
| 参考文档 | modules_design.md 7.5, tech_architecture.md 第五章 |

**任务描述**：
- 审查匿名身份加密存储（AES-256-GCM）
- 审查 user_id → anon_id 映射隔离
- 审查数据脱敏规则（手机号/对话/私聊/树洞）
- 审查管理后台查真实身份的二次认证
- 审查发布时间随机化实现
- 审查互动链脱钩（匿名互动不推到实名通知流，好友关系与匿名身份完全隔离）
- 修复发现的安全问题

**产出物**：
- 安全审计报告 + 修复代码

**中断点**：
**继续指引**：
**未决问题**：

---

#### T025-C 前端：举报入口实现

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | T014-C, T018, T020, T022 |
| 参考文档 | modules_design.md 7.7 |

**任务描述**：
实现 PRD/modules_design.md 7.7 规定的全部4个举报入口：
- 内容详情页右上角"..."菜单 → 举报（树洞/广场）
- 用户主页右上角"..."菜单 → 举报用户
- 私聊界面右上角"..."菜单 → 举报
- 评论区长按消息 → 举报

举报分类选择：色情低俗 / 广告引流 / 辱骂攻击 / 骚扰 / 诈骗 / 自杀自残倾向 / 其他

**产出物**：
- `frontend/src/components/common/ReportDialog.vue` — 统一举报组件
- 各页面集成举报入口

**中断点**：
**继续指引**：
**未决问题**：

---

## 阶段三：测试与部署

### 15. 账户注销（跨模块）

#### T026 后端：账户注销 + 全量数据删除

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005, T011, T021-A |
| 参考文档 | modules_design.md 3.5 |

**任务描述**：
- 账户注销申请 API
- 30 天冷静期机制（冷静期内登录可恢复）
- 冷静期到期后永久删除：用户信息、日记、AI 对话记录、好友关系、动态、举报记录
- 删除前二次确认

**API 端点**：
```
POST   /api/v1/users/me/deactivate    # 申请注销
POST   /api/v1/users/me/reactivate     # 冷静期内恢复
DELETE /api/v1/users/me                # 冷静期后永久删除（内部定时任务触发）
```

**产出物**：
- `backend/services/account_service.py`
- `backend/services/scheduler.py` — 新增冷静期到期检查任务

**中断点**：
**继续指引**：
**未决问题**：

---

### 16. 验证门控与数据看板

#### T027 后端：数据统计 API（验证门控支撑）

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | Backend Architect |
| 状态 | ⏳ |
| 前置依赖 | T005, T008, T011, T013-A |
| 参考文档 | PRD 第六章 阶段一验证门控 |

**任务描述**：
实现阶段一验证门控所需的数据统计 API（PRD 明确要求）：
- 7日留存率统计
- 日均对话轮次统计
- 情绪日记7日连续记录率
- 内测 NPS 收集 API
- 用户行为事件表（为 P2 等级/成就系统预留事件触发架构）

**验证门控标准**（PRD 第六章）：
| 指标 | 目标 | 失败处理 |
|------|------|---------|
| 7日留存率 | ≥ 30% | < 15% 暂停社交层开发 |
| 日均对话轮次 | ≥ 10轮 | 回到AI体验优化 |
| 情绪日记7日连续记录率 | ≥ 20% | 优化日记引导 |
| 内测NPS | ≥ 30 | < 0 重新评估产品方向 |

**产出物**：
- `backend/routers/stats.py`
- `backend/services/stats_service.py`
- `backend/models/user_events.py` — 用户行为事件模型

**中断点**：
**继续指引**：
**未决问题**：

---

### 17. 内测与公测

#### T028-A 内测版打包与分发

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 负责智能体 | DevOps Automator + Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | 阶段一全部任务（T001-T016） + CP1 + CP2 |
| 参考文档 | PRD 第六章 阶段一 W11-W12 |

**任务描述**：
- Android APK 打包（阶段一必须交付）
- iOS TestFlight 分发（如有开发者账号）
- 内测环境部署（使用测试阶段配置：MinIO + 本地关键词过滤 + 极光免费额度 + GLM免费额度）
- 10-20 人内测反馈收集机制
- 运行验证门控指标收集

**产出物**：
- 内测版 APK / TestFlight 链接
- 内测反馈收集表单

**中断点**：
**继续指引**：
**未决问题**：

---

#### T028-B 公测版打包与分发

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | DevOps Automator + Frontend Developer |
| 状态 | ⏳ |
| 前置依赖 | 阶段二全部任务 + CP3 + T025-A/B/C |
| 参考文档 | PRD 第六章 阶段二 W22-W24 |

**任务描述**：
- 阶段二完整版本打包
- 100-200 人公测
- 公测 Bug 修复跟踪
- 数据分析报告 + 下阶段规划

**产出物**：
- 公测版安装包
- 公测报告

**中断点**：
**继续指引**：
**未决问题**：

---

### 18. 测试

#### T029 API 测试

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | API Tester |
| 状态 | ⏳ |
| 前置依赖 | 阶段一+阶段二全部后端任务 |
| 参考文档 | tech_architecture.md 第三章 |

**任务描述**：
- 全部 API 端点功能测试
- 错误码覆盖测试
- 速率限制测试
- 认证/授权边界测试
- 青少年模式拦截测试（受限接口返回 USER_UNDERAGE）
- WebSocket 连接稳定性测试
- 性能基准测试

**产出物**：
- 测试报告

**中断点**：
**继续指引**：
**未决问题**：

---

### 17. 部署

#### T030 部署配置完善

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | DevOps Automator |
| 状态 | ⏳ |
| 前置依赖 | T029 |
| 参考文档 | tech_architecture.md 第六章 |

**任务描述**：
- 完善 Docker Compose 生产配置
- Nginx HTTPS 配置 + 管理后台域名配置
- Uptime Kuma 监控 + 钉钉告警
- 数据备份方案（MySQL binlog + Redis AOF + 每周 OSS 异地备份）
- CI/CD 基础流水线

**产出物**：
- 生产环境部署配置
- 监控配置

**中断点**：
**继续指引**：
**未决问题**：

---

### 19. 阶段二检查点

#### CP3 阶段二代码审查

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 负责智能体 | Code Reviewer |
| 状态 | ⏳ |
| 前置依赖 | T017-T024 全部完成 |

**任务描述**：
- 重点审查 WebSocket 安全、匿名身份隔离
- 审查内容审核实现完整性
- 审查 AI 服务调用安全性
- 输出审查意见和修复清单

**产出物**：
- 代码审查报告

**中断点**：
**继续指引**：
**未决问题**：

---

## 合规里程碑（非开发任务，但需跟踪）

| 里程碑 | 优先级 | 时间 | 说明 |
|--------|--------|------|------|
| 公司注册 | P0 | 上线前 8 周 | 购买域名、注册公司 |
| ICP 备案 | P0 | 上线前 8 周 | 域名备案 |
| 内容审核备案 | P0 | 上线前 6 周 | 向网信办备案审核机制 |
| 隐私政策 | P0 | 上线前 4 周 | 找律师审核，约 2000-5000 元 |
| 算法推荐备案 | P1 | 阶段二后 | MVP 用规则推荐避免触发 |

---

## 执行记录

### 阶段一

| 时间 | 任务ID | 智能体 | 结果 | 产出物路径 |
|------|--------|--------|------|-----------|
| 2026-04-24 | T001 | Frontend Developer | ✅ 完成 | frontend/ |
| 2026-04-24 | T002 | Backend Architect | ✅ 完成 | backend/ |
| 2026-04-24 | T002-测试 | API Tester | ✅ 78/78通过 | 修复1个配置优先级缺陷 |
| 2026-04-24 | T002-审核 | Code Reviewer | ✅ 有条件通过→修复后通过 | 修复7个问题(3严重+4建议)，79/79测试通过 |
| 2026-04-24 | T003 | DevOps Automator | ✅ 完成 | docker-compose.yml, nginx/, mysql/, .env.example |
| 2026-04-25 | T004 | Backend Architect | ✅ 完成 | backend/app/models/, backend/alembic/ (19张表) |
| 2026-04-25 | T005-M | Backend Architect | ✅ 完成 | backend/app/services/ (6个服务模块+图片处理) |
| 2026-04-25 | T005 | Backend Architect | ✅ 完成 | 认证模块(6个API + JWT + 加密 + 青少年模式) |
| 2026-04-25 | T006 | Frontend Developer | ✅ 完成 | 前端登录/注册页(5个页面+2个composable+青少年模式完整实现) |
| 2026-04-25 | T006-A | AI Engineer | ✅ 完成 | docs/ai_eval_scenarios.md(50场景)+docs/ai_eval_report.md(评测框架) |
| 2026-04-25 | T007-A | AI Engineer | ✅ 完成 | backend/app/services/ai_chat.py(MockAIChat 30关键词×3性格+SSE+危机) |
| 2026-04-25 | T007-B | AI Engineer | ✅ 完成 | GLMChatService+SSE流式+重试机制+ai_config.py |
| 2026-04-25 | T007-C | AI Engineer | ✅ 完成 | 3性格Prompt+ai_persona.py+时间段开场白 |

### 阶段二

| 时间 | 任务ID | 智能体 | 结果 | 产出物路径 |
|------|--------|--------|------|-----------|
| - | - | - | - | - |

### 阶段三

| 时间 | 任务ID | 智能体 | 结果 | 产出物路径 |
|------|--------|--------|------|-----------|
| - | - | - | - | - |

### 中断记录

| 时间 | 任务ID | 中断原因 | 中断点 | 继续指引 | 接手智能体 |
|------|--------|---------|--------|---------|-----------|
| 2026-04-24 | T002 | 会话中断 | 基础骨架已搭建，8项子任务未完成 | 已接续完成 | Backend Architect |

---

## 任务总览

| 阶段 | 任务范围 | P0 | P1 | 子任务数 |
|------|---------|----|----|---------|
| 阶段一 | T001-T016 | 15 | 0 | 29 |
| 阶段二社交 | T017-T024 | 3 | 8 | 15 |
| 阶段二安全审核 | T025-A/B/C | 3 | 0 | 3 |
| 阶段三测试部署 | T026-T030 | 1 | 2 | 5 |
| 检查点 | CP1-CP3 | 2 | 1 | 3 |
| **合计** | | **24** | **11** | **55** |

---

> 最后更新：2026-04-24
> 版本：v3.1 — 修复审查问题：新增 T006-A AI评测/T016 首页路由守卫/T017-D 小程序适配，补充 T013-B 社交能量重置/T023-A 他人信息API+社交暴露级别API，T002 补充 APScheduler 初始化，T005-M 补充图片处理服务
