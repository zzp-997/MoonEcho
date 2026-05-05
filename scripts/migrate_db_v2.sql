-- ============================================================
-- 回声（Echo Meet）数据库增量迁移脚本
-- 用途：将旧版 init.sql 创建的数据库升级到当前模型对齐版本
-- 使用：在 MySQL 中直接执行此脚本
-- 注意：执行前请备份数据库！
-- ============================================================

USE `echo_meet`;
SET time_zone = '+08:00';

-- ============================================================
-- users 表变更
-- ============================================================

-- 1. phone 字段长度从 VARCHAR(20) 扩展到 VARCHAR(200)（AES-256-GCM 加密后密文更长）
ALTER TABLE `users` MODIFY COLUMN `phone` VARCHAR(200) NOT NULL COMMENT '手机号（AES-256-GCM 加密）';

-- 2. 移除 phone 字段的唯一约束（密文每次加密结果不同，不可比较）
-- MySQL 约束名可能是 users_phone_key 或自定义名称
ALTER TABLE `users` DROP INDEX `phone`;

-- 3. avatar_url 字段从 TEXT 修改为 VARCHAR(500)
ALTER TABLE `users` MODIFY COLUMN `avatar_url` VARCHAR(500) COMMENT '头像URL';

-- 4. age_range 字段从 VARCHAR(20) 修改为 VARCHAR(10)
ALTER TABLE `users` MODIFY COLUMN `age_range` VARCHAR(10) COMMENT '年龄段：18-24/25-30/31-40/40+';

-- 5. occupation 字段从 VARCHAR(100) 修改为 VARCHAR(50)
ALTER TABLE `users` MODIFY COLUMN `occupation` VARCHAR(50) COMMENT '职业';

-- 6. 添加 guardian_phone 字段（监护人手机号）
ALTER TABLE `users` ADD COLUMN `guardian_phone` VARCHAR(20) COMMENT '监护人手机号' AFTER `is_minor`;

-- 7. 删除旧版 ban_expires_at 字段（如果存在），改用 ban_reason + ban_until
-- 先检查是否存在旧字段并删除
ALTER TABLE `users` DROP COLUMN `ban_expires_at`;

-- 8. 添加封禁相关字段
ALTER TABLE `users` ADD COLUMN `is_banned` TINYINT(1) DEFAULT 0 COMMENT '是否被封禁' AFTER `guardian_phone`;
ALTER TABLE `users` ADD COLUMN `ban_reason` VARCHAR(500) COMMENT '封禁原因' AFTER `is_banned`;
ALTER TABLE `users` ADD COLUMN `ban_until` DATETIME COMMENT '封禁结束时间（null表示永久封禁）' AFTER `ban_reason`;

-- 9. 添加勿扰模式字段
ALTER TABLE `users` ADD COLUMN `do_not_disturb_until` DATETIME COMMENT '勿扰模式结束时间' AFTER `last_active_at`;
ALTER TABLE `users` ADD COLUMN `auto_dnd_enabled` TINYINT(1) DEFAULT 1 COMMENT '是否允许自动勿扰' AFTER `do_not_disturb_until`;
ALTER TABLE `users` ADD COLUMN `dnd_energy_threshold` INT DEFAULT 20 COMMENT '触发自动勿扰的能量阈值' AFTER `auto_dnd_enabled`;

-- 10. 添加 deleted_at 软删除字段
ALTER TABLE `users` ADD COLUMN `deleted_at` DATETIME COMMENT '删除时间，软删除时记录' AFTER `is_active`;

-- 11. 删除旧版 social_exposure_level 和 boundary_settings 字段（已迁移到独立表）
ALTER TABLE `users` DROP COLUMN `social_exposure_level`;
ALTER TABLE `users` DROP COLUMN `boundary_settings`;

-- 12. 添加新索引
ALTER TABLE `users` ADD INDEX `idx_users_is_banned` (`is_banned`);
ALTER TABLE `users` ADD INDEX `idx_users_is_minor` (`is_minor`);
ALTER TABLE `users` ADD INDEX `idx_users_last_active` (`last_active_at`);
ALTER TABLE `users` ADD INDEX `idx_users_is_active` (`is_active`);
ALTER TABLE `users` ADD INDEX `idx_users_do_not_disturb` (`do_not_disturb_until`);

-- ============================================================
-- user_tags 表变更
-- ============================================================

-- 旧版字段名 tag_name/tag_type/confidence/source 对应新版 tag_key/tag_value
-- 需要重建表结构（字段名不兼容）
ALTER TABLE `user_tags` CHANGE COLUMN `tag_name` `tag_key` VARCHAR(50) NOT NULL COMMENT '标签键，如 interest、personality';
ALTER TABLE `user_tags` CHANGE COLUMN `tag_type` `tag_value` VARCHAR(100) NOT NULL COMMENT '标签值';
ALTER TABLE `user_tags` DROP COLUMN `confidence`;
ALTER TABLE `user_tags` DROP COLUMN `source`;

-- 添加唯一约束
ALTER TABLE `user_tags` ADD UNIQUE KEY `uk_user_tags_user_tag_key` (`user_id`, `tag_key`);
ALTER TABLE `user_tags` ADD INDEX `idx_user_tags_tag_key` (`tag_key`);
ALTER TABLE `user_tags` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- anonymous_identities 表变更
-- ============================================================

-- 旧版有 user_id 字段，新版改为 encrypted_user_id（加密存储，无外键）
ALTER TABLE `anonymous_identities` DROP FOREIGN KEY `anonymous_identities_ibfk_1`;
ALTER TABLE `anonymous_identities` CHANGE COLUMN `user_id` `encrypted_user_id` VARCHAR(200) NOT NULL COMMENT '加密的用户ID（AES-256-GCM）';
ALTER TABLE `anonymous_identities` CHANGE COLUMN `anon_avatar` `anon_avatar_url` VARCHAR(500) COMMENT '匿名头像URL';
ALTER TABLE `anonymous_identities` CHANGE COLUMN `personality_tag` `persona_type` VARCHAR(30) COMMENT '人设类型：listener/venter/thinker 等';
ALTER TABLE `anonymous_identities` ADD COLUMN `deleted_at` DATETIME COMMENT '删除时间，软删除时记录' AFTER `is_active`;
ALTER TABLE `anonymous_identities` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';
ALTER TABLE `anonymous_identities` ADD INDEX `idx_anon_identities_encrypted_user_id` (`encrypted_user_id`);
ALTER TABLE `anonymous_identities` DROP COLUMN `expires_at`;

-- ============================================================
-- user_anon_mapping 表变更
-- ============================================================

-- 旧版有 user_id 字段，新版改为 user_id_hash + encrypted_user_id
ALTER TABLE `user_anon_mapping` DROP FOREIGN KEY `user_anon_mapping_ibfk_1`;
ALTER TABLE `user_anon_mapping` DROP FOREIGN KEY `user_anon_mapping_ibfk_2`;
ALTER TABLE `user_anon_mapping` DROP INDEX `uk_user_anon`;
ALTER TABLE `user_anon_mapping` CHANGE COLUMN `user_id` `user_id_hash` VARCHAR(64) NOT NULL COMMENT '用户ID哈希（加盐SHA-256）';
ALTER TABLE `user_anon_mapping` ADD COLUMN `encrypted_user_id` VARCHAR(200) NOT NULL COMMENT '加密的用户ID（AES-256-GCM）' AFTER `user_id_hash`;
ALTER TABLE `user_anon_mapping` ADD COLUMN `scene` VARCHAR(30) NOT NULL COMMENT '使用场景：treehole/square/chat' AFTER `anon_identity_id`;
ALTER TABLE `user_anon_mapping` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';
ALTER TABLE `user_anon_mapping` ADD UNIQUE KEY `uk_user_anon_mapping_user_scene` (`user_id_hash`, `scene`);
ALTER TABLE `user_anon_mapping` ADD INDEX `idx_user_anon_mapping_user_id_hash` (`user_id_hash`);
ALTER TABLE `user_anon_mapping` ADD INDEX `idx_user_anon_mapping_anon_id` (`anon_identity_id`);
ALTER TABLE `user_anon_mapping` DROP COLUMN `mapping_key`;
ALTER TABLE `user_anon_mapping` ADD CONSTRAINT `fk_user_anon_mapping_anon_id` FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`) ON DELETE CASCADE;

-- ============================================================
-- treehole_posts 表变更
-- ============================================================

-- 旧版有 anon_identity_id 指向 anonymous_identities，新版改为 encrypted_user_id
-- 需要先添加 encrypted_user_id，再删除旧外键
ALTER TABLE `treehole_posts` ADD COLUMN `encrypted_user_id` VARCHAR(200) NOT NULL COMMENT '加密的用户ID（AES-256-GCM）' AFTER `id`;
ALTER TABLE `treehole_posts` ADD INDEX `idx_treehole_posts_encrypted_user_id` (`encrypted_user_id`);
ALTER TABLE `treehole_posts` ADD COLUMN `deleted_at` DATETIME COMMENT '删除时间，软删除时记录' AFTER `is_active`;
ALTER TABLE `treehole_posts` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- treehole_comments 表变更
-- ============================================================

-- 添加 anon_identity_id 外键和索引
ALTER TABLE `treehole_comments` ADD COLUMN `anon_identity_id` CHAR(36) COMMENT '匿名身份ID' AFTER `post_id`;
ALTER TABLE `treehole_comments` ADD INDEX `idx_treehole_comments_anon_id` (`anon_identity_id`);
ALTER TABLE `treehole_comments` ADD CONSTRAINT `fk_treehole_comments_anon_identity_id` FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`) ON DELETE SET NULL;
ALTER TABLE `treehole_comments` ADD COLUMN `deleted_at` DATETIME COMMENT '删除时间，软删除时记录' AFTER `is_active`;
ALTER TABLE `treehole_comments` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- posts 表变更
-- ============================================================

ALTER TABLE `posts` ADD COLUMN `deleted_at` DATETIME COMMENT '删除时间，软删除时记录' AFTER `is_active`;
ALTER TABLE `posts` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER `deleted_at`;

-- ============================================================
-- post_comments 表变更
-- ============================================================

ALTER TABLE `post_comments` ADD COLUMN `deleted_at` DATETIME COMMENT '删除时间，软删除时记录' AFTER `is_active`;

-- ============================================================
-- emotion_diaries 表变更
-- ============================================================

ALTER TABLE `emotion_diaries` ADD COLUMN `deleted_at` DATETIME COMMENT '删除时间，软删除时记录' AFTER `is_active`;

-- ============================================================
-- ai_conversations 表变更
-- ============================================================

ALTER TABLE `ai_conversations` ADD COLUMN `title` VARCHAR(100) COMMENT '会话标题' AFTER `ai_persona`;
ALTER TABLE `ai_conversations` ADD COLUMN `last_message_at` DATETIME COMMENT '最后消息时间' AFTER `is_active`;
ALTER TABLE `ai_conversations` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- ai_messages 表变更
-- ============================================================

-- 旧版只有 is_crisis/crisis_type，新版改为更详细的危机字段
ALTER TABLE `ai_messages` ADD COLUMN `crisis_level` VARCHAR(10) COMMENT '危机级别：low/medium/high' AFTER `content`;
ALTER TABLE `ai_messages` ADD COLUMN `crisis_keywords` VARCHAR(200) COMMENT '匹配到的危机关键词（逗号分隔）' AFTER `crisis_level`;
ALTER TABLE `ai_messages` ADD COLUMN `crisis_status` VARCHAR(20) DEFAULT 'pending' COMMENT '危机状态：pending/intervening/resolved/false_positive' AFTER `crisis_keywords`;
ALTER TABLE `ai_messages` ADD COLUMN `crisis_resolved_by` CHAR(36) COMMENT '处理人ID' AFTER `crisis_status`;
ALTER TABLE `ai_messages` ADD COLUMN `crisis_resolution_note` TEXT COMMENT '处理备注' AFTER `crisis_resolved_by`;
ALTER TABLE `ai_messages` ADD COLUMN `crisis_resolved_at` DATETIME COMMENT '处理时间' AFTER `crisis_resolution_note`;
ALTER TABLE `ai_messages` ADD CONSTRAINT `fk_ai_messages_crisis_resolved_by` FOREIGN KEY (`crisis_resolved_by`) REFERENCES `admins`(`id`) ON DELETE SET NULL;
ALTER TABLE `ai_messages` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';
-- 删除旧版字段
ALTER TABLE `ai_messages` DROP COLUMN `is_crisis`;
ALTER TABLE `ai_messages` DROP COLUMN `crisis_type`;

-- ============================================================
-- ai_memories 表变更
-- ============================================================

-- 旧版有 importance DECIMAL(3,2)，新版改为 importance INT
ALTER TABLE `ai_memories` MODIFY COLUMN `content` TEXT NOT NULL COMMENT '记忆内容';
ALTER TABLE `ai_memories` CHANGE COLUMN `importance` `importance` INT DEFAULT 5 COMMENT '重要度 1~10';
ALTER TABLE `ai_memories` ADD COLUMN `access_count` INT DEFAULT 0 COMMENT '被召回次数' AFTER `expires_at`;
ALTER TABLE `ai_memories` ADD COLUMN `last_accessed_at` DATETIME COMMENT '最后被召回时间' AFTER `access_count`;
ALTER TABLE `ai_memories` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- conversations 表变更
-- ============================================================

ALTER TABLE `conversations` ADD COLUMN `friendship_id` CHAR(36) COMMENT '好友关系ID' AFTER `id`;
ALTER TABLE `conversations` ADD CONSTRAINT `fk_conversations_friendship_id` FOREIGN KEY (`friendship_id`) REFERENCES `friendships`(`id`) ON DELETE SET NULL;
ALTER TABLE `conversations` ADD COLUMN `last_message_at` DATETIME COMMENT '最后消息时间' AFTER `user_id_2`;
ALTER TABLE `conversations` ADD COLUMN `last_message_preview` VARCHAR(200) COMMENT '最后消息预览' AFTER `last_message_at`;
ALTER TABLE `conversations` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- chat_messages 表变更
-- ============================================================

ALTER TABLE `chat_messages` ADD COLUMN `message_type` VARCHAR(20) DEFAULT 'text' COMMENT '消息类型：text/image/voice' AFTER `sender_id`;
ALTER TABLE `chat_messages` ADD COLUMN `read_at` DATETIME COMMENT '已读时间' AFTER `is_read`;
ALTER TABLE `chat_messages` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- notifications 表变更
-- ============================================================

ALTER TABLE `notifications` MODIFY COLUMN `title` VARCHAR(100) NOT NULL COMMENT '通知标题';
ALTER TABLE `notifications` ADD COLUMN `read_at` DATETIME COMMENT '已读时间' AFTER `is_read`;
ALTER TABLE `notifications` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- push_records 表变更
-- ============================================================

ALTER TABLE `push_records` ADD COLUMN `notification_id` CHAR(36) COMMENT '关联通知ID' AFTER `user_id`;
ALTER TABLE `push_records` ADD COLUMN `device_token` VARCHAR(200) COMMENT '设备推送Token' AFTER `push_type`;
ALTER TABLE `push_records` ADD COLUMN `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/sent/failed' AFTER `device_token`;
ALTER TABLE `push_records` ADD COLUMN `error_message` VARCHAR(500) COMMENT '错误信息' AFTER `sent_at`;
ALTER TABLE `push_records` ADD CONSTRAINT `fk_push_records_notification_id` FOREIGN KEY (`notification_id`) REFERENCES `notifications`(`id`) ON DELETE SET NULL;
ALTER TABLE `push_records` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- admins 表变更
-- ============================================================

ALTER TABLE `admins` MODIFY COLUMN `role` VARCHAR(20) DEFAULT 'admin' COMMENT '角色：super_admin/admin/operator';
ALTER TABLE `admins` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- reports 表变更
-- ============================================================

ALTER TABLE `reports` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================================
-- user_boundary_settings 表（如果不存在则创建）
-- ============================================================

CREATE TABLE IF NOT EXISTS `user_boundary_settings` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `allow_stranger_messages` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '是否允许陌生人发消息',
    `require_friend_for_chat` TINYINT(1) DEFAULT 0 NOT NULL COMMENT '是否需要是好友才能聊天',
    `show_online_status` TINYINT(1) DEFAULT 0 NOT NULL COMMENT '是否显示在线状态',
    `show_read_status` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '是否显示已读状态',
    `auto_block_on_report` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '举报后自动屏蔽',
    `auto_dnd_on_low_energy` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '能量耗尽时自动勿扰',
    `dnd_energy_threshold` INT DEFAULT 20 NOT NULL COMMENT '触发自动勿扰的能量阈值',
    `show_safety_tips` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '是否显示安全提示',
    `safety_tip_interval_hours` INT DEFAULT 24 NOT NULL COMMENT '安全提示间隔（小时）',
    `quiet_hours_enabled` TINYINT(1) DEFAULT 0 NOT NULL COMMENT '是否开启静默时段',
    `quiet_hours_start` VARCHAR(5) DEFAULT '22:00' COMMENT '静默时段开始（HH:MM）',
    `quiet_hours_end` VARCHAR(5) DEFAULT '07:00' COMMENT '静默时段结束（HH:MM）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_user_boundary_settings_user_id` (`user_id`),
    INDEX `idx_user_boundary_settings_user_id` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- nps_records 表（如果不存在则创建）
-- ============================================================

CREATE TABLE IF NOT EXISTS `nps_records` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `score` INT NOT NULL COMMENT 'NPS 评分（0-10 分）',
    `feedback` JSON COMMENT '用户反馈（可选）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_nps_records_user_id` (`user_id`),
    INDEX `idx_nps_records_created_at` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 迁移完成
-- ============================================================

SELECT 'echo_meet 数据库增量迁移完成（已与 SQLAlchemy 模型对齐）' AS status;
