#!/bin/bash
# ============================================================
# 回声（Echo Meet）数据恢复脚本
# 功能：MySQL 恢复 / Redis 恢复
# ============================================================

set -e

# 配置参数
BACKUP_DIR="${BACKUP_DIR:-/backup}"
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-echo_app}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-echo_app_2026}"
MYSQL_DATABASE="${MYSQL_DATABASE:-echo_meet}"

REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# ============================================================
# 函数：列出可用备份
# ============================================================
list_backups() {
    echo "可用的 MySQL 备份:"
    echo "--------------------------------------------------"
    ls -lh "${BACKUP_DIR}/mysql/"*.sql.gz 2>/dev/null || echo "无 MySQL 备份文件"

    echo ""
    echo "可用的 Redis 备份:"
    echo "--------------------------------------------------"
    ls -lh "${BACKUP_DIR}/redis/"*.rdb 2>/dev/null || echo "无 Redis RDB 备份文件"
    ls -lh "${BACKUP_DIR}/redis/appendonly.aof" 2>/dev/null || echo "无 Redis AOF 文件"
}

# ============================================================
# 函数：MySQL 数据恢复
# ============================================================
restore_mysql() {
    local backup_file="$1"

    if [ -z "$backup_file" ]; then
        echo "错误：未指定备份文件"
        echo "用法: $0 restore_mysql <备份文件路径>"
        return 1
    fi

    if [ ! -f "$backup_file" ]; then
        echo "错误：备份文件不存在: $backup_file"
        return 1
    fi

    echo "警告：此操作将覆盖现有数据库数据！"
    echo "备份文件: $backup_file"
    read -p "确认继续？(yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "已取消恢复操作"
        return 0
    fi

    echo "开始 MySQL 数据恢复..."

    # 解压备份文件
    local sql_file="${backup_file%.gz}"

    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "$sql_file"
    fi

    # 恢复数据
    docker exec -i echo_meet_mysql mysql \
        -u"${MYSQL_USER}" \
        -p"${MYSQL_PASSWORD}" \
        "${MYSQL_DATABASE}" < "$sql_file"

    echo "MySQL 数据恢复完成"

    # 清理临时文件
    rm -f "$sql_file"
}

# ============================================================
# 函数：Redis 数据恢复
# ============================================================
restore_redis() {
    local backup_file="$1"

    if [ -z "$backup_file" ]; then
        echo "错误：未指定备份文件"
        echo "用法: $0 restore_redis <备份文件路径>"
        return 1
    fi

    if [ ! -f "$backup_file" ]; then
        echo "错误：备份文件不存在: $backup_file"
        return 1
    fi

    echo "警告：此操作将覆盖现有 Redis 数据！"
    echo "备份文件: $backup_file"
    read -p "确认继续？(yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "已取消恢复操作"
        return 0
    fi

    echo "开始 Redis 数据恢复..."

    # 停止 Redis 服务
    docker stop echo_meet_redis

    # 替换 RDB 文件
    docker cp "$backup_file" echo_meet_redis:/data/dump.rdb

    # 启动 Redis 服务
    docker start echo_meet_redis

    # 等待 Redis 启动
    sleep 5

    # 验证恢复
    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec echo_meet_redis redis-cli -a "${REDIS_PASSWORD}" ping
    else
        docker exec echo_meet_redis redis-cli ping
    fi

    echo "Redis 数据恢复完成"
}

# ============================================================
# 函数：恢复最近备份
# ============================================================
restore_latest() {
    echo "恢复最近备份..."

    # 找到最近的 MySQL 备份
    local latest_mysql=$(ls -t "${BACKUP_DIR}/mysql/"*.sql.gz 2>/dev/null | head -1)

    if [ -n "$latest_mysql" ]; then
        echo "最近的 MySQL 备份: $latest_mysql"
        restore_mysql "$latest_mysql"
    else
        echo "无可用 MySQL 备份"
    fi

    # 找到最近的 Redis 备份
    local latest_redis=$(ls -t "${BACKUP_DIR}/redis/"*.rdb 2>/dev/null | head -1)

    if [ -n "$latest_redis" ]; then
        echo "最近的 Redis 备份: $latest_redis"
        restore_redis "$latest_redis"
    else
        echo "无可用 Redis 备份"
    fi
}

# ============================================================
# 主函数
# ============================================================
main() {
    local action="$1"

    case "$action" in
        "list")
            list_backups
            ;;
        "restore_mysql")
            restore_mysql "$2"
            ;;
        "restore_redis")
            restore_redis "$2"
            ;;
        "restore_latest")
            restore_latest
            ;;
        *)
            echo "用法: $0 {list|restore_mysql|restore_redis|restore_latest} [参数]"
            echo ""
            echo "命令说明:"
            echo "  list              - 列出可用备份"
            echo "  restore_mysql     - 恢复 MySQL 数据"
            echo "  restore_redis     - 恢复 Redis 数据"
            echo "  restore_latest    - 恢复最近备份"
            exit 1
            ;;
    esac
}

main "$@"