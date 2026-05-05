#!/bin/bash
# ============================================================
# 回声（Echo Meet）数据备份脚本
# 功能：MySQL 备份 / Redis 备份 / OSS 异地备份
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

# OSS 配置（异地备份）
OSS_ENABLED="${OSS_ENABLED:-false}"
OSS_ENDPOINT="${OSS_ENDPOINT:-}"
OSS_BUCKET="${OSS_BUCKET:-}"
OSS_ACCESS_KEY="${OSS_ACCESS_KEY:-}"
OSS_SECRET_KEY="${OSS_SECRET_KEY:-}"

# 保留策略
LOCAL_RETENTION_DAYS="${LOCAL_RETENTION_DAYS:-30}"
OSS_RETENTION_WEEKS="${OSS_RETENTION_WEEKS:-12}"

# 钉钉告警
DINGTALK_ALERT_SCRIPT="${DINGTALK_ALERT_SCRIPT:-./scripts/dingtalk_alert.sh}"

# 日期时间
DATE=$(date '+%Y-%m-%d')
TIME=$(date '+%H%M%S')
DATE_TIME="${DATE}_${TIME}"

# ============================================================
# 函数：MySQL 全量备份
# ============================================================
backup_mysql() {
    echo "开始 MySQL 备份..."

    local backup_file="${BACKUP_DIR}/mysql/echo_meet_${DATE_TIME}.sql.gz"
    local log_file="${BACKUP_DIR}/mysql/backup_${DATE_TIME}.log"

    mkdir -p "${BACKUP_DIR}/mysql"

    # 使用 mysqldump 进行备份
    docker exec echo_meet_mysql mysqldump \
        -u"${MYSQL_USER}" \
        -p"${MYSQL_PASSWORD}" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --flush-logs \
        --master-data=2 \
        "${MYSQL_DATABASE}" 2>> "$log_file" | gzip > "$backup_file"

    # 检查备份是否成功
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        echo "MySQL 备份完成: $backup_file (大小: $size)"

        # 发送成功通知
        $DINGTALK_ALERT_SCRIPT backup MySQL success "备份文件: $backup_file\n大小: $size\n时间: $(date '+%Y-%m-%d %H:%M:%S')"
    else
        echo "错误：MySQL 备份失败"
        $DINGTALK_ALERT_SCRIPT backup MySQL failed "备份失败，请检查日志: $log_file"
        return 1
    fi

    # 清理过期备份
    find "${BACKUP_DIR}/mysql" -name "*.sql.gz" -mtime +${LOCAL_RETENTION_DAYS} -delete
    find "${BACKUP_DIR}/mysql" -name "*.log" -mtime +${LOCAL_RETENTION_DAYS} -delete
}

# ============================================================
# 函数：MySQL Binlog 备份
# ============================================================
backup_mysql_binlog() {
    echo "开始 MySQL Binlog 备份..."

    local binlog_dir="${BACKUP_DIR}/mysql/binlog"

    mkdir -p "$binlog_dir"

    # 复制 binlog 文件
    docker exec echo_meet_mysql sh -c "
        for f in /var/lib/mysql/mysql-bin.*; do
            if [ -f \"\$f\" ]; then
                cp \"\$f\" /backup/mysql/binlog/
            fi
        done
    "

    echo "MySQL Binlog 备份完成"
}

# ============================================================
# 函数：Redis 备份
# ============================================================
backup_redis() {
    echo "开始 Redis 备份..."

    local backup_file="${BACKUP_DIR}/redis/dump_${DATE_TIME}.rdb"
    local aof_file="${BACKUP_DIR}/redis/appendonly.aof"

    mkdir -p "${BACKUP_DIR}/redis"

    # 触发 Redis RDB 保存
    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec echo_meet_redis redis-cli -a "${REDIS_PASSWORD}" BGSAVE
    else
        docker exec echo_meet_redis redis-cli BGSAVE
    fi

    # 等待备份完成
    sleep 5

    # 复制 RDB 文件
    docker cp echo_meet_redis:/data/dump.rdb "$backup_file" 2>/dev/null || echo "RDB 文件不存在"

    # 复制 AOF 文件（如果存在）
    docker cp echo_meet_redis:/data/appendonly.aof "$aof_file" 2>/dev/null || echo "AOF 文件不存在"

    # 检查备份是否成功
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        echo "Redis 备份完成: $backup_file (大小: $size)"

        $DINGTALK_ALERT_SCRIPT backup Redis success "备份文件: $backup_file\n大小: $size"
    else
        echo "警告：Redis RDB 备份文件不存在或为空"
        $DINGTALK_ALERT_SCRIPT backup Redis warning "RDB 备份文件不存在，AOF 持久化仍在运行"
    fi

    # 清理过期备份
    find "${BACKUP_DIR}/redis" -name "*.rdb" -mtime +${LOCAL_RETENTION_DAYS} -delete
}

# ============================================================
# 函数：OSS 异地备份
# ============================================================
backup_to_oss() {
    if [ "$OSS_ENABLED" != "true" ]; then
        echo "OSS 异地备份未启用，跳过"
        return 0
    fi

    echo "开始 OSS 异地备份..."

    # 检查 OSS 工具
    if ! command -v ossutil &> /dev/null; then
        echo "警告：ossutil 未安装，跳过 OSS 备份"
        return 0
    fi

    # 配置 ossutil
    ossutil config -e "$OSS_ENDPOINT" -i "$OSS_ACCESS_KEY" -k "$OSS_SECRET_KEY"

    # 上传 MySQL 备份
    local mysql_backup="${BACKUP_DIR}/mysql/echo_meet_${DATE_TIME}.sql.gz"
    if [ -f "$mysql_backup" ]; then
        ossutil cp "$mysql_backup" "oss://${OSS_BUCKET}/backup/mysql/echo_meet_${DATE}.sql.gz"
        echo "MySQL 备份已上传到 OSS"
    fi

    # 上传 Redis 备份
    local redis_backup="${BACKUP_DIR}/redis/dump_${DATE_TIME}.rdb"
    if [ -f "$redis_backup" ]; then
        ossutil cp "$redis_backup" "oss://${OSS_BUCKET}/backup/redis/dump_${DATE}.rdb"
        echo "Redis 备份已上传到 OSS"
    fi

    # 清理 OSS 过期备份（保留 12 周）
    ossutil rm "oss://${OSS_BUCKET}/backup/mysql/" --recursive --exclude "*.sql.gz" --include "echo_meet_*.sql.gz" --older-than "${OSS_RETENTION_WEEKS}w" --quiet
    ossutil rm "oss://${OSS_BUCKET}/backup/redis/" --recursive --exclude "*.rdb" --include "dump_*.rdb" --older-than "${OSS_RETENTION_WEEKS}w" --quiet

    echo "OSS 异地备份完成"
}

# ============================================================
# 函数：备份验证
# ============================================================
verify_backup() {
    echo "验证备份完整性..."

    # MySQL 备份验证
    local mysql_backup="${BACKUP_DIR}/mysql/echo_meet_${DATE_TIME}.sql.gz"
    if [ -f "$mysql_backup" ]; then
        # 检查 gzip 文件完整性
        if gzip -t "$mysql_backup" 2>/dev/null; then
            echo "MySQL 备份文件完整性验证通过"
        else
            echo "错误：MySQL 备份文件损坏"
            $DINGTALK_ALERT_SCRIPT backup MySQL failed "备份文件完整性验证失败"
            return 1
        fi
    fi

    # Redis 备份验证
    local redis_backup="${BACKUP_DIR}/redis/dump_${DATE_TIME}.rdb"
    if [ -f "$redis_backup" ]; then
        # 检查 RDB 文件大小（至少应该有数据）
        local size=$(stat -c%s "$redis_backup" 2>/dev/null || stat -f%z "$redis_backup")
        if [ "$size" -gt 100 ]; then
            echo "Redis 备份文件验证通过"
        else
            echo "警告：Redis 备份文件过小，可能不完整"
        fi
    fi

    echo "备份验证完成"
}

# ============================================================
# 函数：备份报告
# ============================================================
generate_report() {
    local report_file="${BACKUP_DIR}/backup_report_${DATE_TIME}.txt"

    echo "生成备份报告..."

    cat > "$report_file" << EOF
============================================================
回声（Echo Meet）数据备份报告
============================================================

备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份类型: 全量备份

MySQL 备份:
  文件: ${BACKUP_DIR}/mysql/echo_meet_${DATE_TIME}.sql.gz
  大小: $(du -h "${BACKUP_DIR}/mysql/echo_meet_${DATE_TIME}.sql.gz" 2>/dev/null | cut -f1 || echo "N/A")

Redis 备份:
  RDB 文件: ${BACKUP_DIR}/redis/dump_${DATE_TIME}.rdb
  AOF 文件: ${BACKUP_DIR}/redis/appendonly.aof
  大小: $(du -h "${BACKUP_DIR}/redis/dump_${DATE_TIME}.rdb" 2>/dev/null | cut -f1 || echo "N/A")

OSS 上传:
  状态: ${OSS_ENABLED}

保留策略:
  本地保留: ${LOCAL_RETENTION_DAYS} 天
  OSS 保留: ${OSS_RETENTION_WEEKS} 周

============================================================
备份完成
============================================================
EOF

    echo "备份报告生成完成: $report_file"
}

# ============================================================
# 主函数
# ============================================================
main() {
    echo "=================================================="
    echo "回声（Echo Meet）数据备份任务"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================================="

    # 创建备份目录
    mkdir -p "${BACKUP_DIR}/mysql"
    mkdir -p "${BACKUP_DIR}/redis"

    # 执行备份
    backup_mysql
    backup_mysql_binlog
    backup_redis

    # OSS 异地备份
    backup_to_oss

    # 验证备份
    verify_backup

    # 生成报告
    generate_report

    echo "=================================================="
    echo "备份任务完成"
    echo "=================================================="
}

main