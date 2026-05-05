# 回声 APP - 公测版分发方案

> 文档版本：v1.0
> 创建日期：2026-05-03
> 适用阶段：公测版（100-200人）
> 优先级：H5 > 微信小程序 > Android APK > iOS TestFlight

---

## 一、分发平台总览

| 平台 | 优先级 | 分发方式 | 公测可行性 | 预计触达人数 |
|------|--------|---------|-----------|------------|
| H5 | P0 - 最高 | Nginx 静态托管 + 域名 | 立即可用 | 100-200 |
| 微信小程序 | P0 - 最高 | 提交体验版/审核 | 需审核 1-7 天 | 100-200 |
| Android APK | P1 - 高 | 下载链接 + 二维码 | 需云打包 | 50-100 |
| iOS TestFlight | P2 - 中 | TestFlight 邀请 | 需 Apple 开发者账号 | 10-50 |

---

## 二、H5 分发方案（立即可执行）

### 2.1 架构

```
用户浏览器
    |
    v
Nginx (反向代理 + 静态资源托管)
    |
    +-- /           → 前端静态文件 (dist/build/h5/)
    +-- /api/       → FastAPI 后端 (api:8000)
    +-- /api/v1/ws/ → WebSocket 后端
```

### 2.2 域名配置

| 域名 | 用途 | 指向 |
|------|------|------|
| beta.huisheng.app | H5 前端 | Nginx 服务器 IP |
| beta-api.huisheng.app | API 后端 | Nginx 服务器 IP（同上，通过路径区分） |

**DNS 记录配置**：

```
# A 记录
beta.huisheng.app       →  服务器公网IP
beta-api.huisheng.app   →  服务器公网IP
```

### 2.3 Nginx 配置（公测环境）

在现有 `nginx/nginx.conf` 基础上，添加 H5 公测域名配置：

```nginx
# 公测环境 H5 服务
server {
    listen 80;
    server_name beta.huisheng.app;

    # 健康检查
    location /health {
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # SSE 流式响应代理（AI 对话）
    location ~ ^/api/v1/ai/chat/stream {
        limit_req zone=sse burst=5 nodelay;
        limit_conn conn_limit 5;

        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding on;

        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        add_header X-Accel-Buffering no;
        add_header Cache-Control no-cache;
    }

    # WebSocket 代理
    location /api/v1/ws/ {
        proxy_pass http://api_backend/api/v1/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;
    }

    # API 代理
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        limit_conn conn_limit 20;

        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # H5 前端静态资源
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;

        # SPA 路由支持
        # index.html 不缓存，确保更新后立即生效
        location = /index.html {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }

        # 静态资源长期缓存（文件名含 hash）
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }
}
```

### 2.4 SSL 证书配置（HTTPS）

公测环境必须启用 HTTPS，微信小程序和部分浏览器 API 强制要求。

**使用 Let's Encrypt 免费证书**：

```bash
# 安装 certbot
apt-get install certbot

# 获取证书（先停止 Nginx）
certbot certonly --standalone -d beta.huisheng.app -d beta-api.huisheng.app

# 证书文件位置
# /etc/letsencrypt/live/beta.huisheng.app/fullchain.pem
# /etc/letsencrypt/live/beta.huisheng.app/privkey.pem

# 自动续期（crontab）
0 0 1 * * certbot renew --quiet && docker compose restart nginx
```

**Nginx HTTPS 配置**：

```nginx
server {
    listen 443 ssl http2;
    server_name beta.huisheng.app;

    ssl_certificate /etc/letsencrypt/live/beta.huisheng.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/beta.huisheng.app/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 其余配置与 HTTP 相同...
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name beta.huisheng.app;
    return 301 https://$host$request_uri;
}
```

### 2.5 Docker 部署命令

```bash
# 1. 构建前端
cd frontend
npm run build:h5

# 2. 配置环境
cp ../.env.beta ../.env

# 3. 启动所有服务
cd ..
docker compose up -d --build

# 4. 验证
curl -I https://beta.huisheng.app/health
curl -I https://beta.huisheng.app/api/v1/health
```

### 2.6 H5 分发方式

**方式一：直接链接**
- URL: `https://beta.huisheng.app`
- 添加到手机主屏幕（PWA 效果）

**方式二：二维码**
- 使用二维码生成工具，将 URL 生成二维码
- 公测用户扫码直接访问

---

## 三、微信小程序分发方案

### 3.1 前置条件

| 条件 | 状态 | 说明 |
|------|------|------|
| 微信小程序 AppID | 待申请 | [mp.weixin.qq.com](https://mp.weixin.qq.com) 注册 |
| 微信开发者工具 | 需安装 | [下载地址](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html) |
| 小程序备案 | 需完成 | 2023年9月起必须备案 |
| 服务器域名配置 | 需配置 | 小程序后台 → 开发 → 开发设置 |

### 3.2 服务器域名配置

在小程序管理后台配置以下域名：

| 域名类型 | 域名 | 用途 |
|---------|------|------|
| request 合法域名 | `https://beta-api.huisheng.app` | API 请求 |
| socket 合法域名 | `wss://beta-api.huisheng.app` | WebSocket 私聊 |
| uploadFile 合法域名 | `https://beta-api.huisheng.app` | 图片上传 |
| downloadFile 合法域名 | `https://beta-api.huisheng.app` | 图片下载 |

### 3.3 体验版分发（立即可用）

无需审核，适合公测分发：

1. **构建小程序**：
   ```bash
   cd frontend
   npm run build:mp-weixin
   ```

2. **上传体验版**：
   - 打开微信开发者工具
   - 导入项目：`frontend/dist/build/mp-weixin/`
   - 填写 AppID
   - 点击"上传"按钮
   - 填写版本号：1.0.0-beta
   - 填写备注：公测版 v1.0.0-beta

3. **添加体验者**：
   - 登录小程序管理后台
   - 管理 → 成员管理 → 体验成员
   - 添加公测用户微信号（最多 100 人体验成员）
   - **注意**：体验版有 100 人限制，可通过分批添加解决

4. **分享体验版**：
   - 在小程序管理后台 → 版本管理 → 体验版
   - 生成体验版二维码
   - 分享给体验成员

### 3.4 提交审核（正式版）

提交审核后所有用户可用，无人数限制：

1. 在版本管理中，将体验版提交审核
2. 填写审核信息：
   - 功能页面：首页、AI对话、情绪日记、树洞、广场
   - 测试账号：提供测试手机号
   - 功能描述：每个核心功能的使用说明
3. 审核时间：1-7 个工作日
4. 审核通过后发布上线

### 3.5 小程序审核注意事项

| 注意项 | 说明 |
|--------|------|
| 用户隐私 | 必须添加隐私协议弹窗 |
| 内容安全 | 树洞/广场内容需有审核机制 |
| 青少年模式 | 必须实现青少年模式（已有） |
| 危机干预 | 心理健康相关功能需说明 |
| 匿名功能 | 说明匿名机制，防止滥用 |
| 无虚拟支付 | 小程序内不能有虚拟商品购买 |

---

## 四、Android APK 分发方案

### 4.1 构建流程

详见 `docs/android-build-guide.md`

```bash
# 1. 使用 HBuilderX 云打包生成 APK
# 2. 复制 APK 到分发目录
cp ~/unpackage/apk/huisheng__1.0.0-beta.apk dist/beta/huisheng-1.0.0-beta.apk
```

### 4.2 分发方式

**方式一：直接下载链接**

将 APK 放置在 Nginx 可访问的静态目录下：

```nginx
# nginx.conf 添加 APK 下载路径
location /download/ {
    alias /usr/share/nginx/download/;
    autoindex on;

    # APK 文件类型
    types {
        application/vnd.android.package-archive apk;
    }
}
```

```bash
# 创建下载目录并放置 APK
mkdir -p /usr/share/nginx/download/
cp dist/beta/huisheng-1.0.0-beta.apk /usr/share/nginx/download/
```

下载链接：`https://beta.huisheng.app/download/huisheng-1.0.0-beta.apk`

**方式二：二维码下载**

使用二维码生成工具，将下载链接生成二维码，公测用户扫码下载安装。

**方式三：蒲公英/fir.im 分发平台**

适合更专业的内测分发：
1. 注册 [蒲公英](https://www.pgyer.com/) 或 [fir.im](https://fir.im/)
2. 上传 APK
3. 获取下载页链接和二维码
4. 可设置安装密码，限制下载次数

### 4.3 安装引导

由于使用测试证书，安装时需要引导用户开启"未知来源安装"：

```
安装步骤：
1. 扫码下载 APK
2. 打开下载的 APK 文件
3. 如提示"未知来源"，前往设置 → 安全 → 允许安装未知来源
4. 完成安装
5. 打开回声APP
```

---

## 五、iOS TestFlight 分发方案

### 5.1 前置条件

| 条件 | 说明 |
|------|------|
| Apple 开发者账号 | $99/年，[developer.apple.com](https://developer.apple.com) |
| macOS 电脑 | 打包 iOS 需要 Xcode |
| HBuilderX | 本地打包或云打包 iOS |

### 5.2 流程

1. **注册 Apple 开发者账号**（如已有可跳过）
2. **创建 App ID**：
   - 登录 Apple Developer → Certificates, Identifiers & Profiles
   - 注册 App ID：`com.huisheng.app`
3. **创建证书和描述文件**：
   - 创建开发证书 (.p12)
   - 创建开发描述文件 (.mobileprovision)
4. **HBuilderX 云打包 iOS**：
   - 将 .p12 和 .mobileprovision 导入 HBuilderX
   - 发行 → 原生App-云打包 → 选择 iOS
5. **上传到 App Store Connect**：
   - 使用 Transporter 上传 IPA
6. **TestFlight 分发**：
   - App Store Connect → TestFlight
   - 添加内部测试员（最多 100 人）
   - 或添加外部测试员（需 Beta App Review，最多 10000 人）
7. **测试员安装**：
   - 在 iOS 设备安装 TestFlight App
   - 通过邀请链接加入测试
   - 安装回声测试版

### 5.3 注意事项

- iOS 云打包必须有 Apple 开发者账号
- TestFlight 外部测试需要 Apple 审核（1-2 天）
- 内部测试员最多 100 人（团队开发者账号成员）
- 外部测试员最多 10000 人，但需要 Beta App Review
- 公测阶段建议使用内部测试 + 外部测试组合

---

## 六、分发渠道汇总

### 6.1 公测用户分发矩阵

| 用户类型 | 推荐渠道 | 备选渠道 | 预计人数 |
|---------|---------|---------|---------|
| 普通用户（H5） | H5 网页链接 | 二维码 | 80-150 |
| 微信用户 | 微信小程序体验版 | H5 网页 | 50-100 |
| Android 用户 | APK 下载链接 | 蒲公英分发 | 30-80 |
| iOS 用户 | TestFlight | H5 网页 | 10-30 |

### 6.2 分发二维码生成

为每个渠道生成专属二维码：

```bash
# H5 二维码
https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://beta.huisheng.app

# APK 下载二维码
https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://beta.huisheng.app/download/huisheng-1.0.0-beta.apk
```

### 6.3 公测用户引导页面

建议创建一个简单的公测引导页面 `beta.html`，包含所有渠道的入口：

```
回声 APP 公测版
================

方式一：网页版（推荐）
扫码或点击链接 → https://beta.huisheng.app
支持：手机浏览器、微信内置浏览器

方式二：微信小程序
扫码体验微信小程序版
（需体验成员权限）

方式三：Android APP
扫码下载 APK 安装包
（需开启未知来源安装）

方式四：iOS TestFlight
通过 TestFlight 安装
（需邀请链接）
```

---

## 七、监控与运维

### 7.1 服务监控

| 监控项 | 工具 | 告警阈值 |
|--------|------|---------|
| API 可用性 | Uptime Kuma | 连续 3 次检测失败 |
| API 响应时间 | Uptime Kuma | P99 > 3s |
| 服务器 CPU | Docker Stats | > 80% |
| 服务器内存 | Docker Stats | > 85% |
| 磁盘空间 | Docker Stats | > 90% |
| MySQL 连接数 | MySQL Metrics | > 150 |

### 7.2 日志管理

```bash
# 查看服务日志
docker compose logs -f api --tail 100
docker compose logs -f nginx --tail 100

# 查看 Nginx 访问日志（含响应时间）
docker compose exec nginx tail -f /var/log/nginx/access.log

# 查看 API 错误日志
docker compose logs api | grep ERROR
```

### 7.3 应急响应

| 场景 | 响应动作 | 预期恢复时间 |
|------|---------|------------|
| API 服务不可用 | `docker compose restart api` | < 1 分钟 |
| Nginx 不可用 | `docker compose restart nginx` | < 30 秒 |
| MySQL 连接池耗尽 | `docker compose restart api mysql` | < 2 分钟 |
| 磁盘空间不足 | 清理 Docker 日志和旧镜像 | < 5 分钟 |
| SSL 证书过期 | `certbot renew && docker compose restart nginx` | < 2 分钟 |

---

> 最后更新：2026-05-03
> 版本：v1.0 - 公测版分发方案初始化
