#!/bin/bash
# ============================================================
# 回声（Echo Meet）钉钉告警发送脚本
# 功能：发送服务告警通知到钉钉群
# ============================================================

set -e

# 钉钉配置
DINGTALK_WEBHOOK="${DINGTALK_WEBHOOK:-}"
DINGTALK_SECRET="${DINGTALK_SECRET:-}"

# 告警级别颜色
declare -A LEVEL_COLORS=(
    ["critical"]="🔴"
    ["warning"]="🟡"
    ["info"]="🟢"
)

# ============================================================
# 函数：计算钉钉签名
# ============================================================
sign_dingtalk() {
    local timestamp="$1"
    local secret="$2"

    if [ -z "$secret" ]; then
        return 0
    fi

    # HMAC-SHA256 签名
    local sign_string="${timestamp}\n${secret}"
    local signature=$(echo -n "$sign_string" | openssl dgst -sha256 -hmac "$secret" -binary | base64)
    echo "$signature"
}

# ============================================================
# 函数：发送钉钉消息
# ============================================================
send_dingtalk() {
    local level="$1"
    local title="$2"
    local content="$3"

    if [ -z "$DINGTALK_WEBHOOK" ]; then
        echo "错误：未配置钉钉 Webhook"
        return 1
    fi

    local timestamp=$(date +%s%3N)
    local sign=$(sign_dingtalk "$timestamp" "$DINGTALK_SECRET")

    local level_icon="${LEVEL_COLORS[$level]}"
    local time_str=$(date '+%Y-%m-%d %H:%M:%S')

    # 构建消息体
    local message=$(cat << EOF
{
    "msgtype": "markdown",
    "markdown": {
        "title": "${level_icon} ${title}",
        "text": "${level_icon} **${title}**\n\n**告警级别**: ${level}\n\n**告警时间**: ${time_str}\n\n**告警内容**:\n${content}\n\n---\n\n> 回声（Echo Meet）运维告警系统"
    }
}
EOF
)

    # 发送请求
    local url="${DINGTALK_WEBHOOK}"
    if [ -n "$sign" ]; then
        url="${DINGTALK_WEBHOOK}&timestamp=${timestamp}&sign=${sign}"
    fi

    curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$message"

    echo "钉钉告警已发送: $title"
}

# ============================================================
# 函数：服务故障告警
# ============================================================
alert_service_down() {
    local service_name="$1"
    local details="$2"

    send_dingtalk "critical" \
        "服务故障告警 - ${service_name}" \
        "服务 **${service_name}** 已停止响应\n\n详细信息:\n${details}\n\n请立即检查服务状态！"
}

# ============================================================
# 函数：服务恢复通知
# ============================================================
alert_service_up() {
    local service_name="$1"

    send_dingtalk "info" \
        "服务恢复通知 - ${service_name}" \
        "服务 **${service_name}** 已恢复正常运行"
}

# ============================================================
# 函数：性能告警
# ============================================================
alert_performance() {
    local service_name="$1"
    local metric="$2"
    local value="$3"
    local threshold="$4"

    send_dingtalk "warning" \
        "性能告警 - ${service_name}" \
        "服务 **${service_name}** 性能指标异常\n\n指标: ${metric}\n当前值: ${value}\n阈值: ${threshold}\n\n请关注服务性能状态"
}

# ============================================================
# 函数：数据库备份告警
# ============================================================
alert_backup() {
    local backup_type="$1"
    local status="$2"
    local details="$3"

    local level="info"
    if [ "$status" != "success" ]; then
        level="critical"
    fi

    send_dingtalk "$level" \
        "备份任务通知 - ${backup_type}" \
        "备份类型: ${backup_type}\n状态: ${status}\n详细信息:\n${details}"
}

# ============================================================
# 主函数：根据参数执行不同告警
# ============================================================
main() {
    local action="$1"

    case "$action" in
        "service_down")
            alert_service_down "$2" "$3"
            ;;
        "service_up")
            alert_service_up "$2"
            ;;
        "performance")
            alert_performance "$2" "$3" "$4" "$5"
            ;;
        "backup")
            alert_backup "$2" "$3" "$4"
            ;;
        "test")
            send_dingtalk "info" "测试告警" "这是一条测试告警消息，用于验证钉钉通知配置是否正确"
            ;;
        *)
            echo "用法: $0 {service_down|service_up|performance|backup|test} [参数...]"
            echo ""
            echo "示例:"
            echo "  $0 test                                    # 发送测试告警"
            echo "  $0 service_down MySQL 连接失败             # 服务故障告警"
            echo "  $0 service_up MySQL                        # 服务恢复通知"
            echo "  $0 performance API 响应时间 500ms 300ms    # 性能告警"
            echo "  $0 backup MySQL success 备份文件100MB      # 备份通知"
            exit 1
            ;;
    esac
}

main "$@"