# T030 部署配置完善 - 产出物汇总

## 完成时间
2026-05-03

## 产出物列表

### 1. Docker Compose 生产配置
| 文件 | 说明 |
|------|------|
| `docker-compose.prod.yml` | 生产环境 Docker Compose 配置（资源限制、健康检查、日志配置、安全加固） |

### 2. 数据库配置
| 文件 | 说明 |
|------|------|
| `mysql/my.cnf` | MySQL 生产配置（binlog、InnoDB 优化、慢查询日志、连接池） |
| `redis/redis.conf` | Redis 生产配置（AOF 持久化、RDB 快照、内存管理、安全命令禁用） |

### 3. Nginx 配置
| 文件 | 说明 |
|------|------|
| `nginx/conf.d/echo.conf` | HTTPS 配置 + 双域名配置（api.echomeet.cn + admin.echomeet.cn） |
| `nginx/ssl/README.md` | SSL 证书配置说明（更新为多域名目录结构） |

### 4. 监控告警脚本
| 文件 | 说明 |
|------|------|
| `scripts/setup_monitoring.sh` | Uptime Kuma 监控配置脚本 |
| `scripts/dingtalk_alert.sh` | 钉钉告警发送脚本（服务故障、性能告警、备份通知） |
| `scripts/health_check.sh` | 服务健康检查脚本（HTTP/TCP 检查，状态变化告警） |

### 5. 数据备份脚本
| 文件 | 说明 |
|------|------|
| `scripts/backup.sh` | 数据备份脚本（MySQL 全量、Binlog、Redis RDB/AOF、OSS 上传） |
| `scripts/backup_restore.sh` | 数据恢复脚本（列出备份、恢复 MySQL、恢复 Redis） |
| `docs/backup_guide.md` | 数据备份方案文档（备份策略、恢复流程、常见问题） |

### 6. CI/CD 流水线
| 文件 | 说明 |
|------|------|
| `.github/workflows/main.yml` | CI/CD 主流水线（代码检查、测试、构建、部署） |
| `.github/workflows/test.yml` | 测试流水线（API 测试、安全扫描、性能测试） |
| `.github/workflows/release.yml` | 发布流水线（版本构建、发布包、通知） |
| `docker/nginx.Dockerfile` | Nginx + 前端构建 Dockerfile |

### 7. 部署文档
| 文件 | 说明 |
|------|------|
| `docs/deployment_guide.md` | 部署运维文档（完整部署流程、运维操作、故障排查） |
| `.env.example` | 环境变量模板（新增生产环境配置项） |

---

## 配置要点摘要

### 资源限制配置
```yaml
# docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### MySQL Binlog 配置
```ini
# my.cnf
log_bin = mysql-bin
binlog_format = ROW
binlog_expire_logs_seconds = 604800
sync_binlog = 1
```

### Redis AOF 持久化
```ini
# redis.conf
appendonly yes
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

### HTTPS 安全配置
```nginx
# echo.conf
ssl_protocols TLSv1.2 TLSv1.3;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; ..." always;
```

### CI/CD 流水线阶段
1. **代码检查**：black/isort/mypy + CodeQL 安全扫描
2. **测试**：pytest 单元测试 + 覆盖率报告
3. **构建**：前端构建 + Docker 镜像构建
4. **部署**：公测环境自动部署 + 生产环境手动触发

---

## 部署前检查清单

### 环境变量配置
- [ ] APP_ENV=production
- [ ] DEBUG=false
- [ ] MYSQL_ROOT_PASSWORD（强密码）
- [ ] REDIS_PASSWORD（强密码）
- [ ] JWT_SECRET_KEY（32 字节随机密钥）
- [ ] ANON_MAPPING_ENCRYPTION_KEY（32 字节随机密钥）
- [ ] ZHIPU_API_KEY
- [ ] 阿里云短信/内容审核 AccessKey
- [ ] DINGTALK_WEBHOOK

### SSL 证书
- [ ] api.echomeet.cn 证书已部署
- [ ] admin.echomeet.cn 证书已部署
- [ ] 证书权限已设置为 600

### 监控告警
- [ ] Uptime Kuma 已初始化
- [ ] 监控端点已配置
- [ ] 钉钉机器人已创建
- [ ] 告警测试已通过

### 备份配置
- [ ] 备份目录已创建
- [ ] 备份脚本已测试
- [ ] OSS 配置（可选）已完成
- [ ] 恢复演练已完成

### CI/CD 配置
- [ ] GitHub Secrets 已配置
- [ ] 流水线已触发测试
- [ ] 部署权限已配置

---

## 下一步操作

1. **申请 SSL 证书**：使用 Certbot 申请 Let's Encrypt 证书
2. **配置钉钉告警**：创建钉钉群机器人，获取 Webhook
3. **初始化监控**：访问 Uptime Kuma 界面配置监控端点
4. **测试备份脚本**：执行一次完整备份和恢复演练
5. **配置 CI/CD Secrets**：在 GitHub 项目中配置服务器 SSH 密钥
6. **部署到公测环境**：使用 docker-compose.prod.yml 启动服务