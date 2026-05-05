# MoonEcho 本地开发 + 云端部署指南

> 适用场景：本地开发调试，生产环境部署在阿里云服务器

---

## 一、架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                     阿里云服务器 (118.25.182.15)             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │   MySQL     │  │   Redis     │  │   FastAPI       │   │
│  │   3306      │  │   6379      │  │   8000          │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│  已有容器: howtoai-mysql                                       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     本地开发环境                            │
│  ┌─────────────┐  ┌─────────────┐                        │
│  │   前端      │  │   后端      │                        │
│  │   H5/小程序  │  │   FastAPI   │                        │
│  │   5173      │  │   8000      │                        │
│  └─────────────┘  └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**网络访问：**
- 本地开发环境 → 云服务器 MySQL (端口 3306)
- 本地前端 H5 → 本地后端 (端口 8000，通过 Vite 代理)
- 本地后端 → 云服务器 MySQL

---

## 二、云端准备工作

### 2.1 开放安全组端口

在阿里云控制台 → ECS → 安全组，添加以下规则：

| 方向 | 协议 | 端口 | 来源 | 用途 |
|------|------|------|------|------|
| 入方向 | TCP | 3306 | 本地IP | MySQL 连接 |
| 入方向 | TCP | 8000 | 0.0.0.0/0 | API 访问（可选，生产关闭） |

> 获取本地 IP：`curl ifconfig.me`

### 2.2 创建数据库

SSH 连接到服务器：

```bash
ssh root@118.25.182.15
```

连接 MySQL：

```bash
mysql -u howtoai -pHowtoai2024
# 或
mysql -u root -pHowtoai2024
```

创建 MoonEcho 数据库：

```sql
CREATE DATABASE IF NOT EXISTS moonecho DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'moonecho'@'%' IDENTIFIED BY 'Moonecho2024';
GRANT ALL PRIVILEGES ON moonecho.* TO 'moonecho'@'%';
FLUSH PRIVILEGES;
SHOW DATABASES;
```

### 2.3 初始化数据库表

```bash
# 在服务器上克隆 MoonEcho 项目（如果尚未克隆）
cd /www
git clone https://github.com/your-org/MoonEcho.git
cd MoonEcho/backend

# 安装依赖
pip install -e .

# 执行数据库迁移
alembic upgrade head
```

---

## 三、本地开发配置

### 3.1 前端配置

文件：`frontend/.env.development`

```bash
VITE_API_BASE_URL=/api/v1
```

Vite 代理配置（`vite.config.ts`）已包含：
- `/api` → `http://localhost:8000`
- `/api/v1/ws` → `http://localhost:8000` (WebSocket)
- `/api/v1/ai/chat/stream` → `http://localhost:8000` (SSE)

### 3.2 后端配置

文件：`backend/.env`

```bash
# 数据库 - 连接云端 MySQL
DATABASE_URL=mysql+aiomysql://moonecho:Moonecho2024@118.25.182.15:3306/moonecho

# Redis - 使用云端（如果已配置）或本地
REDIS_URL=redis://118.25.182.15:6379/0
# 如需密码：redis://:password@118.25.182.15:6379/0

# JWT 配置
JWT_SECRET=your-local-dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# CORS - 本地开发允许
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI 服务
AI_PROVIDER=zhipu
ZHIPU_API_KEY=your-zhipu-api-key
```

### 3.3 启动本地开发环境

**后端：**

```bash
cd backend
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端（H5）：**

```bash
cd frontend
pnpm install
pnpm dev:h5
```

访问 `http://localhost:5173`

---

## 四、需要上传到服务器的文件

### 4.1 Docker 部署模式

如果使用 Docker 在服务器部署：

```
MoonEcho/
├── backend/                    # 后端代码
├── frontend/                   # 前端代码
├── docker-compose.yml          # Docker 编排
├── docker-compose.prod.yml     # 生产环境配置
├── nginx/
│   ├── nginx.conf              # Nginx 配置
│   ├── conf.d/                 # 站点配置
│   └── ssl/                    # SSL 证书
├── mysql/
│   └── init.sql                # 数据库初始化
└── scripts/
    └── backup.sh               # 备份脚本
```

**上传方式：**

```bash
# 方式1：Git 拉取（推荐）
cd /www
git clone https://github.com/your-org/MoonEcho.git
git pull origin master

# 方式2：rsync 同步
rsync -avz --exclude='node_modules' --exclude='.git' \
  --exclude='__pycache__' --exclude='*.pyc' \
  ./ root@118.25.182.15:/www/MoonEcho/
```

### 4.2 纯代码部署

不上传依赖目录，只上传源代码：

```bash
# 后端源代码
backend/
├── app/
├── alembic/
├── tests/
├── config/
├── main.py
├── pyproject.toml
└── alembic.ini

# 前端构建产物
frontend/dist/build/h5/
```

---

## 五、生产环境部署

### 5.1 服务器环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 存储 | 50GB | 100GB |
| 带宽 | 5Mbps | 10Mbps |

### 5.2 生产环境变量

文件：`server/.env.prod`

```bash
# 生产环境必须修改以下配置

# 数据库
DATABASE_URL=mysql+aiomysql://moonecho:【强密码】@localhost:3306/moonecho

# Redis（必须设置密码）
REDIS_URL=redis://:【强密码】@localhost:6379/0

# JWT（使用 openssl rand -hex 32 生成）
JWT_SECRET=【32字节随机密钥】

# 加密密钥
ANON_MAPPING_ENCRYPTION_KEY=【32字节随机密钥】

# CORS（只允许自己的域名）
ALLOWED_ORIGINS=https://your-domain.com

# 调试模式
DEBUG=false
```

### 5.3 Docker Compose 启动

```bash
cd /www/MoonEcho

# 复制并编辑环境变量
cp .env.example .env.prod
vi .env.prod

# 启动所有服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### 5.4 Nginx + SSL 配置

```bash
# 申请 Let's Encrypt 证书
certbot certonly --manual --preferred-challenges dns -d api.your-domain.com

# 配置 Nginx
# 编辑 nginx/conf.d/api.conf
```

---

## 六、快速检查清单

### 本地开发
- [ ] 阿里云安全组已开放 3306 端口给本地 IP
- [ ] 已创建 moonecho 数据库和用户
- [ ] backend/.env 已配置云端 MySQL 地址
- [ ] 后端能正常连接云端 MySQL
- [ ] 前端 `pnpm dev:h5` 能正常启动

### 生产部署
- [ ] 所有密码已修改为强密码
- [ ] SSL 证书已配置
- [ ] CORS 只允许自己的域名
- [ ] DEBUG=false
- [ ] 数据库已执行迁移
- [ ] Docker 服务已启动

---

## 七、常见问题

### Q: 连接云端 MySQL 失败
```bash
# 1. 检查安全组是否开放 3306 端口
# 2. 检查 MySQL 用户权限
mysql -u root -p -e "SHOW GRANTS FOR 'moonecho'@'%';"

# 3. 测试端口连通性
telnet 118.25.182.15 3306
```

### Q: 数据库迁移失败
```bash
# 查看详细错误
alembic upgrade head --verbose

# 如果表已存在，尝试降级再升级
alembic downgrade -1
alembic upgrade head
```

### Q: 前端无法访问后端
检查 vite.config.ts 代理配置是否正确，确保后端 CORS 配置包含 `http://localhost:5173`
