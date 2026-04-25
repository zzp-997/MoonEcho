-- ============================================================
-- 回声（Echo Meet）MySQL 初始化脚本
-- 功能：创建数据库 / 设置字符集 / 设置时区
-- ============================================================

-- 设置默认字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `echo_meet`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE `echo_meet`;

-- 设置时区为 UTC+8（中国标准时间）
SET time_zone = '+08:00';

-- ============================================================
-- 核心表结构
-- ============================================================

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
    `id` CHAR(36) PRIMARY KEY,
    `phone` VARCHAR(20) UNIQUE NOT NULL,
    `phone_hash` VARCHAR(64) UNIQUE NOT NULL,
    `nickname` VARCHAR(50),
    `avatar_url` TEXT,
    `age_range` VARCHAR(20),
    `city` VARCHAR(50),
    `occupation` VARCHAR(100),
    `notification_settings` JSON COMMENT '推送偏好设置',
    `is_minor` TINYINT(1) DEFAULT 0 COMMENT '是否未成年用户',
    `social_energy` DECIMAL(5,2) DEFAULT 50.00 COMMENT '社交能量值，范围0-100',
    `social_energy_updated_at` DATETIME COMMENT '社交能量最后更新时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `last_active_at` DATETIME,
    `is_active` TINYINT(1) DEFAULT 1,
    INDEX `idx_users_phone_hash` (`phone_hash`),
    INDEX `idx_users_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户画像标签表
CREATE TABLE IF NOT EXISTS `user_tags` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `tag_name` VARCHAR(50) NOT NULL,
    `tag_type` VARCHAR(20),
    `confidence` DECIMAL(3,2),
    `source` VARCHAR(50),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_tags_user_id` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 匿名身份表
CREATE TABLE IF NOT EXISTS `anonymous_identities` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `anon_nickname` VARCHAR(50) NOT NULL,
    `anon_avatar` TEXT,
    `personality_tag` VARCHAR(50),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `expires_at` DATETIME,
    `is_active` TINYINT(1) DEFAULT 1,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户-匿名身份映射（加密存储）
CREATE TABLE IF NOT EXISTS `user_anon_mapping` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `anon_identity_id` CHAR(36) NOT NULL,
    `mapping_key` VARCHAR(128),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_user_anon` (`user_id`, `anon_identity_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 情绪日记表
CREATE TABLE IF NOT EXISTS `emotion_diaries` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `emotion_tone` VARCHAR(20) NOT NULL,
    `emotion_labels` JSON,
    `content_text` TEXT,
    `content_hash` VARCHAR(64),
    `record_date` DATE NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `is_synced` TINYINT(1) DEFAULT 0,
    `client_id` VARCHAR(50),
    UNIQUE KEY `uk_user_date_client` (`user_id`, `record_date`, `client_id`),
    INDEX `idx_emotion_diaries_user_date` (`user_id`, `record_date` DESC),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 树洞吐槽表
CREATE TABLE IF NOT EXISTS `treehole_posts` (
    `id` CHAR(36) PRIMARY KEY,
    `anon_identity_id` CHAR(36),
    `content` TEXT NOT NULL,
    `topic_tag` VARCHAR(50),
    `image_urls` JSON,
    `resonance_count` INT DEFAULT 0,
    `comment_count` INT DEFAULT 0,
    `status` VARCHAR(20) DEFAULT 'active',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `expires_at` DATETIME,
    INDEX `idx_treehole_posts_created` (`created_at` DESC),
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 树洞评论表
CREATE TABLE IF NOT EXISTS `treehole_comments` (
    `id` CHAR(36) PRIMARY KEY,
    `post_id` CHAR(36) NOT NULL,
    `anon_identity_id` CHAR(36),
    `content` VARCHAR(100) NOT NULL,
    `is_resonance` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_treehole_comments_post` (`post_id`, `created_at`),
    FOREIGN KEY (`post_id`) REFERENCES `treehole_posts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 动态广场表
CREATE TABLE IF NOT EXISTS `posts` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36),
    `anon_identity_id` CHAR(36),
    `is_anonymous` TINYINT(1) DEFAULT 0,
    `content` TEXT NOT NULL,
    `image_urls` JSON,
    `visibility` VARCHAR(20) DEFAULT 'public',
    `like_count` INT DEFAULT 0,
    `comment_count` INT DEFAULT 0,
    `status` VARCHAR(20) DEFAULT 'active',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_posts_user_created` (`user_id`, `created_at` DESC),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 好友关系表
CREATE TABLE IF NOT EXISTS `friendships` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id_1` CHAR(36) NOT NULL,
    `user_id_2` CHAR(36) NOT NULL,
    `status` VARCHAR(20) DEFAULT 'pending',
    `initiator_id` CHAR(36),
    `greeting_message` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_users` (`user_id_1`, `user_id_2`),
    FOREIGN KEY (`user_id_1`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id_2`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 会话表
CREATE TABLE IF NOT EXISTS `conversations` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id_1` CHAR(36) NOT NULL,
    `user_id_2` CHAR(36) NOT NULL,
    `last_message_at` DATETIME,
    `last_message_preview` VARCHAR(100),
    UNIQUE KEY `uk_users` (`user_id_1`, `user_id_2`),
    FOREIGN KEY (`user_id_1`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id_2`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 私聊消息表
CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` CHAR(36) PRIMARY KEY,
    `conversation_id` CHAR(36) NOT NULL,
    `sender_id` CHAR(36),
    `receiver_id` CHAR(36),
    `content` TEXT,
    `message_type` VARCHAR(20) DEFAULT 'text',
    `is_read` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_chat_messages_conversation` (`conversation_id`, `created_at` DESC),
    INDEX `idx_chat_messages_receiver` (`receiver_id`, `is_read`),
    FOREIGN KEY (`sender_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`receiver_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI对话会话表
CREATE TABLE IF NOT EXISTS `ai_conversations` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `ai_persona` VARCHAR(20) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `is_active` TINYINT(1) DEFAULT 1,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI对话消息表
CREATE TABLE IF NOT EXISTS `ai_messages` (
    `id` CHAR(36) PRIMARY KEY,
    `conversation_id` CHAR(36) NOT NULL,
    `role` VARCHAR(20) NOT NULL,
    `content` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_ai_messages_conversation` (`conversation_id`, `created_at` DESC),
    FOREIGN KEY (`conversation_id`) REFERENCES `ai_conversations`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI记忆表
CREATE TABLE IF NOT EXISTS `ai_memories` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `conversation_id` CHAR(36) COMMENT '关联的对话会话ID',
    `memory_type` VARCHAR(30) NOT NULL COMMENT 'short_term/mid_term/long_term/person_info/event',
    `key_facts` JSON COMMENT '记忆内容，结构化存储',
    `importance` DECIMAL(3,2) COMMENT '重要性评分 0-1',
    `source` VARCHAR(50) COMMENT '记忆来源',
    `last_referenced_at` DATETIME COMMENT '最后引用时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `expires_at` DATETIME COMMENT '过期时间',
    INDEX `idx_ai_memories_user_type` (`user_id`, `memory_type`),
    INDEX `idx_ai_memories_conversation` (`conversation_id`),
    INDEX `idx_ai_memories_expires` (`expires_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`conversation_id`) REFERENCES `ai_conversations`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 通知推送表
CREATE TABLE IF NOT EXISTS `notifications` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `type` VARCHAR(30) NOT NULL COMMENT '通知类型',
    `title` VARCHAR(100),
    `content` TEXT,
    `payload` JSON COMMENT '跳转参数',
    `is_read` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_notifications_user_unread` (`user_id`, `is_read`, `created_at` DESC),
    INDEX `idx_notifications_user_created` (`user_id`, `created_at` DESC),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 推送记录表（频率控制）
CREATE TABLE IF NOT EXISTS `push_records` (
    `id` CHAR(36) PRIMARY KEY,
    `user_id` CHAR(36) NOT NULL,
    `push_type` VARCHAR(30) NOT NULL,
    `sent_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_push_records_user_type` (`user_id`, `push_type`, `sent_at` DESC),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 管理员表
CREATE TABLE IF NOT EXISTS `admins` (
    `id` CHAR(36) PRIMARY KEY,
    `username` VARCHAR(50) UNIQUE NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希',
    `nickname` VARCHAR(50),
    `role` VARCHAR(20) DEFAULT 'operator' COMMENT 'super_admin/admin/operator',
    `permissions` JSON COMMENT '权限节点列表',
    `last_login_at` DATETIME,
    `last_login_ip` VARCHAR(45),
    `is_active` TINYINT(1) DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_admins_username` (`username`),
    INDEX `idx_admins_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 操作日志表
CREATE TABLE IF NOT EXISTS `admin_logs` (
    `id` CHAR(36) PRIMARY KEY,
    `admin_id` CHAR(36) NOT NULL,
    `action` VARCHAR(50) NOT NULL COMMENT '操作类型',
    `target_type` VARCHAR(30) COMMENT '操作对象类型',
    `target_id` CHAR(36) COMMENT '操作对象ID',
    `details` JSON COMMENT '操作详情',
    `ip_address` VARCHAR(45) COMMENT '操作者IP',
    `user_agent` VARCHAR(500) COMMENT '浏览器UA',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_admin_logs_admin` (`admin_id`),
    INDEX `idx_admin_logs_action` (`action`),
    INDEX `idx_admin_logs_target` (`target_type`, `target_id`),
    INDEX `idx_admin_logs_created` (`created_at` DESC),
    FOREIGN KEY (`admin_id`) REFERENCES `admins`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 初始化数据
-- ============================================================

-- 插入默认管理员（密码：admin123，需在首次登录后修改）
-- 注意：实际部署时请使用 bcrypt 生成密码哈希
-- INSERT INTO `admins` (`id`, `username`, `password_hash`, `nickname`, `role`, `permissions`)
-- VALUES (UUID(), 'admin', '$2b$12$...', '超级管理员', 'super_admin', '["all"]');

-- 初始化完成
SELECT 'echo_meet 数据库初始化完成' AS status;
