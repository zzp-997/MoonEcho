-- ============================================================
-- 数据库迁移脚本：创建 user_events 表
-- 版本：0014_fix_missing_tables
-- 日期：2026-05-06
--
-- 执行前请先备份数据库！
-- ============================================================

-- 步骤 1：检查 user_events 表是否已存在
-- 如果返回 0，说明表不存在，需要执行后续创建语句
SELECT COUNT(*) AS table_exists
FROM information_schema.tables
WHERE table_schema = DATABASE() AND table_name = 'user_events';

-- 步骤 2：创建 user_events 表
-- 只有当步骤 1 返回 0 时才需要执行
CREATE TABLE IF NOT EXISTS user_events (
    id CHAR(36) PRIMARY KEY COMMENT '主键UUID',
    user_id CHAR(36) NOT NULL COMMENT '用户ID',
    event_type VARCHAR(50) NOT NULL COMMENT '事件类型：diary_created/ai_chat_message/friend_request_sent 等',
    event_data JSON NULL COMMENT '事件附加数据（JSON），不同事件类型携带不同数据结构',
    source VARCHAR(20) NULL COMMENT '事件来源：app/web/mini_program',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_user_events_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户行为事件表';

-- 步骤 3：创建索引
-- 用户维度查询：按用户筛选事件
CREATE INDEX IF NOT EXISTS idx_user_events_user_id ON user_events(user_id);

-- 事件类型维度查询：按事件类型筛选
CREATE INDEX IF NOT EXISTS idx_user_events_event_type ON user_events(event_type);

-- 联合查询：按用户+事件类型组合筛选（统计模块高频查询）
CREATE INDEX IF NOT EXISTS idx_user_events_user_type ON user_events(user_id, event_type);

-- 时间范围查询：按事件发生时间筛选（支持时间窗口统计）
CREATE INDEX IF NOT EXISTS idx_user_events_created_at ON user_events(created_at);

-- 步骤 4：查看当前 alembic 版本
SELECT * FROM alembic_version;

-- 步骤 5：更新 alembic 版本记录（可选）
-- 如果你的迁移链已经正确设置，可以执行以下语句更新版本号
-- 注意：请根据实际情况选择是否执行
-- INSERT INTO alembic_version (version_num) VALUES ('0014')
-- ON DUPLICATE KEY UPDATE version_num = '0014';

-- ============================================================
-- 验证脚本执行结果
-- ============================================================

-- 验证表已创建
SHOW CREATE TABLE user_events;

-- 验证索引已创建
SHOW INDEX FROM user_events;
