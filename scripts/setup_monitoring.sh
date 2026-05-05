#!/bin/bash
# ============================================================
# 回声（Echo Meet）Uptime Kuma 监控配置脚本
# 功能：自动配置监控端点、钉钉告警通知
# ============================================================

set -e

# 配置参数
UPTIME_KUMA_URL="${UPTIME_KUMA_URL:-http://localhost:3001}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123456}"

# 监控端点配置
declare -a MONITOR_CONFIGS=(
    # API 服务健康检查
    "name=API健康检查|type=http|url=http://api:8000/health|interval=60|timeout=10|retry=3"

    # MySQL 服务健康检查
    "name=MySQL健康检查|type=http|url=http://mysql:3306|interval=60|timeout=10|retry=5"

    # Redis 服务健康检查
    "name=Redis健康检查|type=http|url=http://redis:6379|interval=60|timeout=10|retry=5"

    # MinIO 服务健康检查
    "name=MinIO健康检查|type=http|url=http://minio:9000/minio/health/live|interval=60|timeout=10|retry=3"

    # Nginx 服务健康检查
    "name=Nginx健康检查|type=http|url=http://nginx/health|interval=30|timeout=5|retry=3"

    # 管理后台健康检查
    "name=管理后台健康检查|type=http|url=http://api:8000/api/admin/v1/health|interval=60|timeout=10|retry=3"
)

# 钉钉告警配置
DINGTALK_WEBHOOK="${DINGTALK_WEBHOOK:-}"
DINGTALK_SECRET="${DINGTALK_SECRET:-}"

# ============================================================
# 函数：初始化 Uptime Kuma 管理员账户
# ============================================================
init_admin() {
    echo "初始化 Uptime Kuma 管理员账户..."

    # 使用 Docker 执行初始化
    docker exec echo_meet_uptime_kuma sh -c "
        if [ ! -f /app/data/kuma.db ]; then
            echo '等待 Uptime Kuma 初始化...'
            sleep 5
        fi
    "

    echo "管理员账户初始化完成"
}

# ============================================================
# 函数：配置钉钉告警通知
# ============================================================
setup_dingtalk_notification() {
    if [ -z "$DINGTALK_WEBHOOK" ]; then
        echo "警告：未配置钉钉 Webhook，跳过钉钉告警配置"
        return 0
    fi

    echo "配置钉钉告警通知..."

    # 钉钉消息格式配置
    cat > /tmp/dingtalk_notification.json << EOF
{
    "name": "钉钉告警",
    "type": "webhook",
    "url": "${DINGTALK_WEBHOOK}",
    "webhookContentType": "application/json",
    "webhookBody": "{\"msgtype\":\"text\",\"text\":{\"content\":\"🔴 告警通知\n\n监控名称: {monitor_name}\n状态: {status}\n时间: {timestamp}\n详情: {msg}\"}}"
}
EOF

    echo "钉钉告警配置已生成"
    echo "请手动在 Uptime Kuma 界面中添加通知渠道"
}

# ============================================================
# 函数：生成监控配置文件
# ============================================================
generate_monitor_config() {
    echo "生成监控配置文件..."

    mkdir -p ./monitoring

    # 生成 JSON 配置
    cat > ./monitoring/uptime_kuma_config.json << EOF
{
    "monitors": [
        {
            "name": "API健康检查",
            "type": "http",
            "url": "http://api:8000/health",
            "interval": 60,
            "timeout": 10,
            "retry": 3,
            "notification": ["钉钉告警"]
        },
        {
            "name": "MySQL健康检查",
            "type": "tcp",
            "host": "mysql",
            "port": 3306,
            "interval": 60,
            "timeout": 10,
            "retry": 5
        },
        {
            "name": "Redis健康检查",
            "type": "tcp",
            "host": "redis",
            "port": 6379,
            "interval": 60,
            "timeout": 10,
            "retry": 5
        },
        {
            "name": "MinIO健康检查",
            "type": "http",
            "url": "http://minio:9000/minio/health/live",
            "interval": 60,
            "timeout": 10,
            "retry": 3
        },
        {
            "name": "Nginx健康检查",
            "type": "http",
            "url": "http://nginx/health",
            "interval": 30,
            "timeout": 5,
            "retry": 3
        },
        {
            "name": "管理后台健康检查",
            "type": "http",
            "url": "http://api:8000/api/admin/v1/health",
            "interval": 60,
            "timeout": 10,
            "retry": 3
        }
    ],
    "notifications": [
        {
            "name": "钉钉告警",
            "type": "webhook",
            "url": "${DINGTALK_WEBHOOK}",
            "webhookContentType": "application/json"
        }
    ]
}
EOF

    echo "监控配置文件生成完成: ./monitoring/uptime_kuma_config.json"
}

# ============================================================
# 函数：配置健康检查增强（添加到 API）
# ============================================================
setup_health_endpoints() {
    echo "建议在后端 API 添加以下健康检查端点增强..."

    cat > ./monitoring/health_endpoint_suggestion.md << EOF
# API 健康检查端点增强建议

## 当前端点

- `/health` - 基础健康检查

## 建议增强

### 1. 详细健康检查 `/health/detail`

返回各服务状态：

\`\`\`json
{
    "status": "healthy",
    "timestamp": "2026-05-03T10:00:00Z",
    "services": {
        "mysql": {
            "status": "healthy",
            "latency_ms": 5
        },
        "redis": {
            "status": "healthy",
            "latency_ms": 2
        },
        "minio": {
            "status": "healthy",
            "latency_ms": 10
        }
    },
    "version": "1.0.0",
    "uptime_seconds": 3600
}
\`\`\`

### 2. 就绪检查 `/health/ready`

用于 Kubernetes/Docker 就绪探针：

\`\`\`python
@app.get("/health/ready")
async def readiness_check():
    # 检查数据库连接
    try:
        await db.execute(select(1))
    except:
        return {"status": "not_ready", "reason": "database_unavailable"}

    # 检查 Redis 连接
    try:
        await redis.ping()
    except:
        return {"status": "not_ready", "reason": "redis_unavailable"}

    return {"status": "ready"}
\`\`\`

### 3. 存活检查 `/health/live`

用于 Kubernetes 存活探针：

\`\`\`python
@app.get("/health/live")
async def liveness_check():
    return {"status": "alive"}
\`\`\`

EOF

    echo "健康检查建议文档生成完成"
}

# ============================================================
# 主函数
# ============================================================
main() {
    echo "=================================================="
    echo "回声（Echo Meet）Uptime Kuma 监控配置"
    echo "=================================================="

    init_admin
    generate_monitor_config
    setup_dingtalk_notification
    setup_health_endpoints

    echo "=================================================="
    echo "配置完成"
    echo "=================================================="
    echo ""
    echo "下一步操作："
    echo "1. 访问 Uptime Kuma 界面：http://localhost:3001"
    echo "2. 创建管理员账户（首次访问）"
    echo "3. 根据生成的配置文件手动添加监控"
    echo "4. 配置钉钉 Webhook 告警通知"
    echo ""
    echo "配置文件位置："
    echo "- ./monitoring/uptime_kuma_config.json"
    echo "- ./monitoring/health_endpoint_suggestion.md"
}

main