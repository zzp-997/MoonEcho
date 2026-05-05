# ============================================================
# 回声（Echo Meet）API 服务 Dockerfile
# 基于 Python 3.11 + FastAPI + Uvicorn
# 支持：应用启动 + Alembic 数据库迁移
# ============================================================

FROM python:3.11-slim AS base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（gcc 用于编译 C 扩展，curl 用于健康检查）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制整个项目（pyproject.toml + app 目录）
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir . 2>/dev/null || \
    pip install --no-cache-dir -e .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/system/health || exit 1

# 启动命令（由 docker-compose 覆盖，支持数据库迁移后再启动）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
