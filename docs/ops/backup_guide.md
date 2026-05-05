# 回声（Echo Meet）数据备份方案文档

## 1. 备份策略概述

### 1.1 备份类型

| 类型 | 频率 | 保留时间 | 存储位置 |
|------|------|----------|---------|
| MySQL 全量备份 | 每周一次（周日凌晨 3 点） | 本地 30 天 / OSS 12 周 | 本地 + OSS |
| MySQL Binlog | 每日增量 | 7 天 | 本地 |
| Redis RDB | 每周一次 | 本地 30 天 / OSS 12 周 | 本地 + OSS |
| Redis AOF | 实时持久化 | 无限期 | 本地 |

### 1.2 备份窗口

- 全量备份：每周日凌晨 3:00（低流量时段）
- Binlog 增量：每小时同步
- AOF 持久化：实时进行（everysec 模式）

---

## 2. MySQL 备份方案

### 2.1 Binlog 配置（已在 my.cnf 中配置）

```ini
# MySQL 配置文件关键参数
log_bin = mysql-bin
binlog_format = ROW
binlog_expire_logs_seconds = 604800  # 7天
sync_binlog = 1
max_binlog_size = 100M
```

### 2.2 全量备份脚本

位置：`scripts/backup.sh`

执行方式：
```bash
# 手动执行
./scripts/backup.sh

# 或通过 Docker Compose
docker-compose -f docker-compose.prod.yml exec backup ./backup.sh
```

### 2.3 恢复流程

```bash
# 1. 查看可用备份
./scripts/backup_restore.sh list

# 2. 恢复指定备份
./scripts/backup_restore.sh restore_mysql /backup/mysql/echo_meet_2026-05-03_030000.sql.gz

# 3. 恢复最近备份
./scripts/backup_restore.sh restore_latest
```

---

## 3. Redis 备份方案

### 3.1 AOF 持久化配置（已在 redis.conf 中配置）

```ini
# Redis 配置文件关键参数
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

### 3.2 RDB 快照配置

```ini
# RDB 快照策略
save 900 1      # 15分钟内至少1个key变化
save 300 10     # 5分钟内至少10个key变化
save 60 10000   # 1分钟内至少10000个key变化
```

### 3.3 备份脚本执行

```bash
# Redis RDB 备份（包含在 backup.sh 中）
./scripts/backup.sh

# 或手动触发
docker exec echo_meet_redis redis-cli BGSAVE
```

---

## 4. OSS 异地备份

### 4.1 OSS 配置

在 `.env` 文件中配置以下参数：

```bash
OSS_ENABLED=true
OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
OSS_BUCKET=echo-meet-backup
OSS_ACCESS_KEY=<your_access_key>
OSS_SECRET_KEY=<your_secret_key>
```

### 4.2 OSS 工具安装

```bash
# 安装 ossutil（阿里云 OSS 命令行工具）
wget https://gosspublic.alicdn.com/ossutil/1.7.17/ossutil-v1.7.17-linux-amd64.zip
unzip ossutil-v1.7.17-linux-amd64.zip
chmod 755 ossutil
mv ossutil /usr/local/bin/
```

### 4.3 OSS 备份目录结构

```
oss://echo-meet-backup/
├── mysql/
│   ├── echo_meet_2026-05-03.sql.gz
│   ├── echo_meet_2026-05-10.sql.gz
│   └── ...
├── redis/
│   ├── dump_2026-05-03.rdb
│   ├── dump_2026-05-10.rdb
│   └── ...
└── reports/
    ├── backup_report_2026-05-03.txt
    └── ...
```

---

## 5. 定时任务配置

### 5.1 Docker Compose 内置定时任务

在 `docker-compose.prod.yml` 中配置：

```yaml
backup:
  environment:
    - BACKUP_SCHEDULE=0 3 * * 0  # 每周日凌晨3点
  command: sh -c "crontab -l | { cat; echo '0 3 * * 0 /backup.sh'; } | crontab - && crond -f -l 2"
```

### 5.2 外部 Crontab 配置（可选）

```bash
# 编辑 crontab
crontab -e

# 添加备份任务
# 每周日凌晨3点执行全量备份
0 3 * * 0 cd /path/to/MoonEcho && ./scripts/backup.sh >> /var/log/echo_meet_backup.log 2>&1

# 每小时同步 Binlog（如果使用外部备份）
0 * * * * cd /path/to/MoonEcho && ./scripts/binlog_sync.sh >> /var/log/echo_meet_binlog.log 2>&1
```

---

## 6. 监控与告警

### 6.1 备份状态监控

备份脚本会自动发送钉钉通知：

- 备份成功：发送成功通知，包含文件大小和时间
- 备份失败：发送失败告警，需立即处理
- 备份文件损坏：发送完整性验证失败告警

### 6.2 告警配置

在 `.env` 中配置钉钉 Webhook：

```bash
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx
```

---

## 7. 恢复演练建议

### 7.1 定期演练计划

建议每月进行一次恢复演练：

1. 在测试环境恢复备份
2. 验证数据完整性
3. 记录恢复时间
4. 优化恢复流程

### 7.2 恢复演练步骤

```bash
# 1. 创建测试数据库
docker exec echo_meet_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "CREATE DATABASE echo_meet_test"

# 2. 恢复备份到测试库
docker exec -i echo_meet_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} echo_meet_test < /backup/mysql/echo_meet_xxx.sql

# 3. 验证数据
docker exec echo_meet_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT COUNT(*) FROM echo_meet_test.users"

# 4. 清理测试库
docker exec echo_meet_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DROP DATABASE echo_meet_test"
```

---

## 8. 生产环境部署检查清单

- [ ] MySQL binlog 已启用并正常生成
- [ ] Redis AOF 持久化已启用
- [ ] 备份脚本已配置并测试执行
- [ ] OSS 异地备份已配置（可选）
- [ ] 钉钉告警 Webhook 已配置
- [ ] 定时任务已配置并启用
- [ ] 恢复演练已完成至少一次
- [ ] 备份存储空间充足

---

## 9. 常见问题

### Q1: 备份文件过大怎么办？

```bash
# 1. 检查数据库大小
docker exec echo_meet_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "
SELECT table_schema, ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
GROUP BY table_schema
ORDER BY SUM(data_length + index_length) DESC
"

# 2. 清理旧数据（如日志表）
# 3. 增加压缩级别
gzip -9 backup.sql  # 最高压缩级别
```

### Q2: Binlog 空间不足？

```bash
# 清理过期 binlog
docker exec echo_meet_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "PURGE BINARY LOGS BEFORE '2026-04-01 00:00:00'"
```

### Q3: Redis 恢复后数据丢失？

确保 AOF 文件完整性：

```bash
# 检查 AOF 文件
docker exec echo_meet_redis redis-check-aof /data/appendonly.aof

# 如果损坏，尝试修复
docker exec echo_meet_redis redis-check-aof --fix /data/appendonly.aof
```