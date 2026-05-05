#!/bin/bash
# ============================================================
# 回声（Echo Meet）健康检查脚本
# 功能：检查各服务健康状态，触发钉钉告警
# ============================================================

set -e

# 钉钉告警脚本路径
ALERT_SCRIPT="./scripts/dingtalk_alert.sh"

# 服务健康检查端点
declare -A SERVICES=(
    ["API"]="http://localhost:8000/health"
    ["MySQL"]="localhost:3306"
    ["Redis"]="localhost:6379"
    ["MinIO"]="http://localhost:9000/minio/health/live"
    ["Nginx"]="http://localhost/health"
)

# 服务状态记录文件
STATUS_FILE="./monitoring/service_status.json"

# ============================================================
# 函数：检查 HTTP 服务健康
# ============================================================
check_http_health() {
    local service_name="$1"
    local url="$2"
    local timeout="${3:-10}"

    local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null || echo "000")

    if [ "$status" = "200" ]; then
        echo "healthy"
    else
        echo "unhealthy"
    fi
}

# ============================================================
# 函数：检查 TCP 服务健康
# ============================================================
check_tcp_health() {
    local service_name="$1"
    local host="$2"
    local port="$3"
    local timeout="${4:-10}"

    local status=$(timeout "$timeout" bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null && echo "healthy" || echo "unhealthy")

    echo "$status"
}

# ============================================================
# 函数：更新服务状态记录
# ============================================================
update_status() {
    local service_name="$1"
    local status="$2"

    # 初始化状态文件
    if [ ! -f "$STATUS_FILE" ]; then
        echo '{"services":{}}' > "$STATUS_FILE"
    fi

    # 更新状态（使用 jq 或简单 sed）
    local time_str=$(date '+%Y-%m-%d %H:%M:%S')

    # 简单 JSON 更新（不依赖 jq）
    if grep -q "\"$service_name\"" "$STATUS_FILE"; then
        sed -i "s/\"$service_name\": {[^}]*}/\"$service_name\": {\"status\": \"$status\", \"time\": \"$time_str\"}/" "$STATUS_FILE"
    else
        # 添加新服务记录
        sed -i "s/\"services\": {}/\"services\": {\"$service_name\": {\"status\": \"$status\", \"time\": \"$time_str\"}}/" "$STATUS_FILE"
    fi
}

# ============================================================
# 函数：发送告警
# ============================================================
send_alert() {
    local service_name="$1"
    local old_status="$2"
    local new_status="$3"

    if [ "$new_status" = "unhealthy" ] && [ "$old_status" != "unhealthy" ]; then
        # 服务故障
        $ALERT_SCRIPT service_down "$service_name" "服务健康检查失败，请立即排查"
    elif [ "$new_status" = "healthy" ] && [ "$old_status" = "unhealthy" ]; then
        # 服务恢复
        $ALERT_SCRIPT service_up "$service_name"
    fi
}

# ============================================================
# 主函数：执行健康检查
# ============================================================
main() {
    echo "=================================================="
    echo "回声（Echo Meet）服务健康检查"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================================="

    # 初始化状态文件
    mkdir -p ./monitoring

    for service in "${!SERVICES[@]}"; do
        local endpoint="${SERVICES[$service]}"
        local status=""

        echo "检查服务: $service"

        if [[ "$endpoint" =~ ^http ]]; then
            status=$(check_http_health "$service" "$endpoint")
        else
            local host=$(echo "$endpoint" | cut -d: -f1)
            local port=$(echo "$endpoint" | cut -d: -f2)
            status=$(check_tcp_health "$service" "$host" "$port")
        fi

        # 获取旧状态
        local old_status=$(grep -o "\"$service\":.*" "$STATUS_FILE" 2>/dev/null | grep -o '"status": "[^"]*"' | cut -d'"' -f4 || echo "unknown")

        # 更新状态
        update_status "$service" "$status"

        # 发送告警（状态变化时）
        if [ "$status" != "$old_status" ]; then
            send_alert "$service" "$old_status" "$status"
        fi

        echo "  状态: $status"
    done

    echo "=================================================="
    echo "健康检查完成"
    echo "=================================================="
}

main