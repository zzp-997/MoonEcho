# 数据库模型与迁移审查报告

**审查日期**: 2026-05-06
**审查范围**: backend/app/models/*.py vs backend/alembic/versions/*.py

## 一、发现的问题

### 1. 缺失的数据库表

| 表名 | 模型文件 | 发现状态 | 修复迁移 |
|------|----------|----------|----------|
| `post_comments` | post.py | ❌ 缺失 | 0013_posts_tables.py |
| `post_likes` | post.py | ❌ 缺失 | 0013_posts_tables.py |
| `post_favorites` | post.py | ❌ 缺失 | 0013_posts_tables.py |
| `post_follows` | post.py | ❌ 缺失 | 0013_posts_tables.py |
| `user_events` | user_events.py | ❌ 缺失 | 0014_fix_missing_tables.py |

### 2. 缺失的字段

| 表名 | 缺失字段 | 模型定义位置 | 修复迁移 |
|------|----------|--------------|----------|
| `posts` | `anon_identity_id` | post.py:41 | 0013_posts_tables.py |
| `posts` | `favorite_count` | post.py:64 | 0013_posts_tables.py |

### 3. 已确认正确存在的表和字段

| 表名 | 创建迁移 | 备注 |
|------|----------|------|
| `users` | 0001_initial | ✓ |
| `user_tags` | 0001_initial | ✓ |
| `anonymous_identities` | 0001_initial + 0011修改 | 已添加 encrypted_user_id |
| `user_anon_mapping` | 0001_initial + 0011修改 | 已添加 user_id_hash, encrypted_user_id |
| `emotion_diaries` | 0001_initial | ✓ |
| `treehole_posts` | 0001_initial + 0011修改 | 已添加 encrypted_user_id |
| `treehole_comments` | 0001_initial + 0011修改 | 已添加 anon_identity_id |
| `friendships` | 0001_initial + 0008修改 | ✓ |
| `friend_requests` | 0008_friend_system | ✓ |
| `user_blocks` | 0008_friend_system | ✓ |
| `conversations` | 0001_initial | ✓ |
| `chat_messages` | 0001_initial + 0009修改 | 已添加 expires_at |
| `ai_conversations` | 0001_initial | ✓ |
| `ai_messages` | 0001_initial + 0002修改 | 已添加危机检测字段 |
| `ai_memories` | 0001_initial | ✓ |
| `notifications` | 0001_initial | ✓ |
| `push_records` | 0001_initial | ✓ |
| `admins` | 0001_initial | ✓ |
| `admin_logs` | 0001_initial | ✓ |
| `reports` | 0001_initial | ✓ |
| `weekly_reports` | 0003_weekly_reports | ✓ |
| `holidays` | 0005_holidays | ✓ |
| `user_holidays` | 0005_holidays | ✓ |
| `penalty_records` | 0010_penalty_records | ✓ |
| `device_bans` | 0010_penalty_records | ✓ |
| `user_boundary_settings` | 0010_user_boundary_settings | ✓ |
| `nps_records` | 0012_nps_records | ✓ |

## 二、迁移版本链

```
0001_initial
├── 0002_ai_message_crisis_fields
├── 0003_weekly_reports
├── 0004_notification_settings
├── 0005_holidays
├── 0006_user_ban_fields
├── 0007_phone_field_security_fix
├── 0008_friend_system
├── 0009_chat_message_expires_at
├── 0010 (penalty_records, device_bans)
├── 0010_user_boundary_settings
├── 0011_anon_security_fix
├── 0012_nps_records
├── 0013_posts_tables ← 新增
└── 0014_fix_missing_tables ← 新增
```

## 三、错误根因分析

### errodtxt.md 中的接口错误

| 接口 | 错误原因 |
|------|----------|
| `/api/v1/users/me/social-level` | 依赖 `post_likes`、`post_comments`、`post_follows` 表进行行为统计，这些表不存在 |
| `/api/v1/users/me/profile-tags` | 可能依赖用户行为数据 |
| `/api/v1/friend-requests` | 需要确认 `friend_requests` 表是否创建（迁移未执行） |
| `/api/v1/posts` | `posts` 表缺少 `anon_identity_id`、`favorite_count` 字段，且缺少子表 |

## 四、修复方案

### 步骤 1：执行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 步骤 2：验证迁移结果

```bash
# 检查所有表是否创建
alembic current

# 或连接数据库查询
sqlite3 echo.db ".tables"
```

### 步骤 3：验证 API 接口

重新调用以下接口确认问题已修复：
- GET /api/v1/users/me/social-level
- GET /api/v1/users/me/profile-tags
- GET /api/v1/friend-requests
- GET /api/v1/posts

## 五、新增迁移文件

1. **0013_posts_tables.py**
   - 创建 `post_comments` 表
   - 创建 `post_likes` 表
   - 创建 `post_favorites` 表
   - 创建 `post_follows` 表
   - 为 `posts` 表添加 `anon_identity_id` 和 `favorite_count` 字段

2. **0014_fix_missing_tables.py**
   - 创建 `user_events` 表

## 六、预防措施

1. **代码审查规范**：新增模型时必须同步创建迁移文件
2. **CI 检查**：添加模型与迁移匹配检查脚本
3. **迁移测试**：在测试环境先验证迁移文件
