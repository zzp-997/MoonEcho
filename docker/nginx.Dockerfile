# ============================================================
# 回声（Echo Meet）Nginx + 前端 Dockerfile
# 用于 CI/CD 构建包含前端静态资源的 Nginx 镜像
# ============================================================

FROM nginx:alpine AS base

# 安装必要工具
RUN apk add --no-cache curl tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 复制 Nginx 配置
COPY nginx/nginx.conf /etc/nginx/nginx.conf:ro
COPY nginx/conf.d /etc/nginx/conf.d:ro

# 创建必要目录
RUN mkdir -p /var/cache/nginx /var/log/nginx /usr/share/nginx/html /usr/share/nginx/admin /etc/nginx/ssl

# 设置权限
RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx /usr/share/nginx/html /usr/share/nginx/admin

# ----------------------------------------------------------
# 前端构建阶段
# ----------------------------------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制前端源码
COPY frontend/ ./

# 构建前端
RUN npm run build:h5

# ----------------------------------------------------------
# 管理后台构建阶段
# ----------------------------------------------------------
FROM node:18-alpine AS admin-builder

WORKDIR /app

# 复制管理后台依赖文件
COPY admin-web/package*.json ./

# 安装依赖
RUN npm ci

# 复制管理后台源码
COPY admin-web/ ./

# 构建管理后台
RUN npm run build

# ----------------------------------------------------------
# 最终镜像
# ----------------------------------------------------------
FROM base AS final

# 复制前端构建产物
COPY --from=frontend-builder /app/dist/build/h5 /usr/share/nginx/html

# 复制管理后台构建产物
COPY --from=admin-builder /app/dist /usr/share/nginx/admin

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 暴露端口
EXPOSE 80 443

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]