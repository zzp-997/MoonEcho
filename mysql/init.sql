-- ============================================================
-- 回声（Echo Meet）MySQL 初始化脚本
-- 功能：创建数据库 / 设置字符集 / 设置时区 / 全量表结构
-- 覆盖：阶段一 + 阶段二全部模块
-- 说明：本脚本与 SQLAlchemy 模型定义完全对齐
--       任何模型变更都需同步更新此文件
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
-- 用户系统
-- ============================================================

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `phone` VARCHAR(200) NOT NULL COMMENT '手机号（AES-256-GCM 加密）',
    `phone_hash` VARCHAR(64) UNIQUE NOT NULL COMMENT '手机号哈希（用于唯一索引）',
    `nickname` VARCHAR(50) COMMENT '昵称',
    `avatar_url` VARCHAR(500) COMMENT '头像URL',
    `age_range` VARCHAR(10) COMMENT '年龄段：18-24/25-30/31-40/40+',
    `city` VARCHAR(50) COMMENT '所在城市',
    `occupation` VARCHAR(50) COMMENT '职业',
    `notification_settings` JSON COMMENT '通知偏好设置（JSON）',
    `is_minor` TINYINT(1) DEFAULT 0 COMMENT '是否未成年人',
    `guardian_phone` VARCHAR(20) COMMENT '监护人手机号',
    `is_banned` TINYINT(1) DEFAULT 0 COMMENT '是否被封禁',
    `ban_reason` VARCHAR(500) COMMENT '封禁原因',
    `ban_until` DATETIME COMMENT '封禁结束时间（null表示永久封禁）',
    `social_energy` DECIMAL(5,2) COMMENT '社交能量值 0.00~100.00',
    `social_energy_updated_at` DATETIME COMMENT '社交能量最后更新时间',
    `last_active_at` DATETIME COMMENT '最后活跃时间',
    `do_not_disturb_until` DATETIME COMMENT '勿扰模式结束时间',
    `auto_dnd_enabled` TINYINT(1) DEFAULT 1 COMMENT '是否允许自动勿扰',
    `dnd_energy_threshold` INT DEFAULT 20 COMMENT '触发自动勿扰的能量阈值',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效：1=有效，0=已删除',
    `deleted_at` DATETIME COMMENT '删除时间，软删除时记录',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_users_phone_hash` (`phone_hash`),
    INDEX `idx_users_created` (`created_at`),
    INDEX `idx_users_last_active` (`last_active_at`),
    INDEX `idx_users_is_active` (`is_active`),
    INDEX `idx_users_is_banned` (`is_banned`),
    INDEX `idx_users_is_minor` (`is_minor`),
    INDEX `idx_users_do_not_disturb` (`do_not_disturb_until`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户画像标签表
CREATE TABLE IF NOT EXISTS `user_tags` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `tag_key` VARCHAR(50) NOT NULL COMMENT '标签键，如 interest、personality',
    `tag_value` VARCHAR(100) NOT NULL COMMENT '标签值',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_user_tags_user_tag_key` (`user_id`, `tag_key`),
    INDEX `idx_user_tags_user_id` (`user_id`),
    INDEX `idx_user_tags_tag_key` (`tag_key`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 匿名身份表
CREATE TABLE IF NOT EXISTS `anonymous_identities` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `encrypted_user_id` VARCHAR(200) NOT NULL COMMENT '加密的用户ID（AES-256-GCM）',
    `anon_nickname` VARCHAR(50) NOT NULL COMMENT '匿名昵称',
    `anon_avatar_url` VARCHAR(500) COMMENT '匿名头像URL',
    `persona_type` VARCHAR(30) COMMENT '人设类型：listener/venter/thinker 等',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效：1=有效，0=已删除',
    `deleted_at` DATETIME COMMENT '删除时间，软删除时记录',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_anon_identities_encrypted_user_id` (`encrypted_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户-匿名身份映射（加密存储）
CREATE TABLE IF NOT EXISTS `user_anon_mapping` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id_hash` VARCHAR(64) NOT NULL COMMENT '用户ID哈希（加盐SHA-256）',
    `encrypted_user_id` VARCHAR(200) NOT NULL COMMENT '加密的用户ID（AES-256-GCM）',
    `anon_identity_id` CHAR(36) NOT NULL COMMENT '匿名身份ID',
    `scene` VARCHAR(30) NOT NULL COMMENT '使用场景：treehole/square/chat',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_user_anon_mapping_user_scene` (`user_id_hash`, `scene`),
    INDEX `idx_user_anon_mapping_user_id_hash` (`user_id_hash`),
    INDEX `idx_user_anon_mapping_anon_id` (`anon_identity_id`),
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户边界设置表
CREATE TABLE IF NOT EXISTS `user_boundary_settings` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    -- 消息接收设置
    `allow_stranger_messages` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '是否允许陌生人发消息',
    `require_friend_for_chat` TINYINT(1) DEFAULT 0 NOT NULL COMMENT '是否需要是好友才能聊天',
    -- 隐私设置
    `show_online_status` TINYINT(1) DEFAULT 0 NOT NULL COMMENT '是否显示在线状态',
    `show_read_status` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '是否显示已读状态',
    -- 自动保护设置
    `auto_block_on_report` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '举报后自动屏蔽',
    `auto_dnd_on_low_energy` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '能量耗尽时自动勿扰',
    `dnd_energy_threshold` INT DEFAULT 20 NOT NULL COMMENT '触发自动勿扰的能量阈值',
    -- 安全提示设置
    `show_safety_tips` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '是否显示安全提示',
    `safety_tip_interval_hours` INT DEFAULT 24 NOT NULL COMMENT '安全提示间隔（小时）',
    -- 静默时段设置
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
-- 情绪日记系统
-- ============================================================

-- 情绪日记表
CREATE TABLE IF NOT EXISTS `emotion_diaries` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `emotion_tone` VARCHAR(30) COMMENT '情绪基调：happy/sad/anxious/angry/calm 等',
    `emotion_labels` JSON COMMENT '情绪标签列表（JSON）',
    `content_text` TEXT COMMENT '日记内容（加密存储）',
    `content_hash` VARCHAR(64) COMMENT '内容哈希，用于完整性校验',
    `record_date` DATE NOT NULL COMMENT '记录日期',
    `is_synced` TINYINT(1) DEFAULT 0 COMMENT '是否已同步到服务端',
    `client_id` VARCHAR(50) COMMENT '客户端唯一标识，用于离线同步去重',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效：1=有效，0=已删除',
    `deleted_at` DATETIME COMMENT '删除时间，软删除时记录',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_emotion_diaries_user_date_client` (`user_id`, `record_date`, `client_id`),
    INDEX `idx_emotion_diaries_user_date` (`user_id`, `record_date` DESC),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 树洞系统
-- ============================================================

-- 树洞吐槽表
CREATE TABLE IF NOT EXISTS `treehole_posts` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `encrypted_user_id` VARCHAR(200) NOT NULL COMMENT '加密的用户ID（AES-256-GCM）',
    `anon_identity_id` CHAR(36) COMMENT '匿名身份ID',
    `content` TEXT NOT NULL COMMENT '帖子内容',
    `topic_tag` VARCHAR(50) COMMENT '话题标签',
    `image_urls` JSON COMMENT '图片URL列表（JSON）',
    `resonance_count` INT DEFAULT 0 COMMENT '共鸣数',
    `comment_count` INT DEFAULT 0 COMMENT '评论数',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/expired/deleted',
    `expires_at` DATETIME COMMENT '过期时间',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效：1=有效，0=已删除',
    `deleted_at` DATETIME COMMENT '删除时间，软删除时记录',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_treehole_posts_created` (`created_at` DESC),
    INDEX `idx_treehole_posts_encrypted_user_id` (`encrypted_user_id`),
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 树洞评论表
CREATE TABLE IF NOT EXISTS `treehole_comments` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `post_id` CHAR(36) NOT NULL COMMENT '帖子ID',
    `anon_identity_id` CHAR(36) COMMENT '匿名身份ID',
    `content` VARCHAR(100) NOT NULL COMMENT '评论内容，限制100字',
    `is_resonance` TINYINT(1) DEFAULT 0 COMMENT '是否为共鸣（轻量互动）',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效：1=有效，0=已删除',
    `deleted_at` DATETIME COMMENT '删除时间，软删除时记录',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_treehole_comments_post` (`post_id`, `created_at`),
    INDEX `idx_treehole_comments_anon_id` (`anon_identity_id`),
    FOREIGN KEY (`post_id`) REFERENCES `treehole_posts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 动态广场系统
-- ============================================================

-- 动态广场帖子表
CREATE TABLE IF NOT EXISTS `posts` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `anon_identity_id` CHAR(36) COMMENT '匿名身份ID',
    `content` TEXT NOT NULL COMMENT '动态内容',
    `image_urls` JSON COMMENT '图片URL列表（JSON，最多9张）',
    `is_anonymous` TINYINT(1) DEFAULT 0 COMMENT '是否匿名发布',
    `visibility` VARCHAR(20) DEFAULT 'public' COMMENT '可见性：public/friends/private',
    `like_count` INT DEFAULT 0 COMMENT '共鸣（点赞）数',
    `comment_count` INT DEFAULT 0 COMMENT '评论数',
    `favorite_count` INT DEFAULT 0 COMMENT '收藏数',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效：1=有效，0=已删除',
    `deleted_at` DATETIME COMMENT '删除时间，软删除时记录',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_posts_user_id` (`user_id`),
    INDEX `idx_posts_created` (`created_at` DESC),
    INDEX `idx_posts_visibility` (`visibility`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 动态评论表
CREATE TABLE IF NOT EXISTS `post_comments` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `post_id` CHAR(36) NOT NULL COMMENT '动态ID',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `anon_identity_id` CHAR(36) COMMENT '匿名身份ID',
    `content` VARCHAR(500) NOT NULL COMMENT '评论内容，最多500字',
    `is_anonymous` TINYINT(1) DEFAULT 0 COMMENT '是否匿名评论',
    `reply_to_comment_id` CHAR(36) COMMENT '回复的评论ID',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效：1=有效，0=已删除',
    `deleted_at` DATETIME COMMENT '删除时间，软删除时记录',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_post_comments_post_id` (`post_id`),
    INDEX `idx_post_comments_user_id` (`user_id`),
    INDEX `idx_post_comments_created` (`created_at`),
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`anon_identity_id`) REFERENCES `anonymous_identities`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`reply_to_comment_id`) REFERENCES `post_comments`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 动态共鸣（点赞）记录表
CREATE TABLE IF NOT EXISTS `post_likes` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `post_id` CHAR(36) NOT NULL COMMENT '动态ID',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_post_likes_post_user` (`post_id`, `user_id`),
    INDEX `idx_post_likes_post_id` (`post_id`),
    INDEX `idx_post_likes_user_id` (`user_id`),
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 动态收藏记录表
CREATE TABLE IF NOT EXISTS `post_favorites` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `post_id` CHAR(36) NOT NULL COMMENT '动态ID',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_post_favorites_post_user` (`post_id`, `user_id`),
    INDEX `idx_post_favorites_user_id` (`user_id`),
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 动态悄悄关注记录表
CREATE TABLE IF NOT EXISTS `post_follows` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `post_id` CHAR(36) NOT NULL COMMENT '动态ID',
    `follower_id` CHAR(36) NOT NULL COMMENT '关注者ID',
    `following_id` CHAR(36) NOT NULL COMMENT '被关注者ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_post_follows_follower_following` (`follower_id`, `following_id`),
    INDEX `idx_post_follows_follower_id` (`follower_id`),
    INDEX `idx_post_follows_following_id` (`following_id`),
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`follower_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`following_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 社交系统
-- ============================================================

-- 好友申请表（必须在 friendships 之前创建，因 friendships.request_id 有外键依赖）
CREATE TABLE IF NOT EXISTS `friend_requests` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `sender_id` CHAR(36) NOT NULL COMMENT '发送者用户ID',
    `recipient_id` CHAR(36) NOT NULL COMMENT '接收者用户ID',
    `greeting_message` VARCHAR(200) COMMENT '打招呼语',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/accepted/rejected/expired',
    `expires_at` DATETIME NOT NULL COMMENT '过期时间（申请发送后7天）',
    `handled_at` DATETIME COMMENT '处理时间',
    `request_number` INT DEFAULT 1 COMMENT '申请序号（同一用户对的第几次申请）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_friend_requests_sender_recipient_number` (`sender_id`, `recipient_id`, `request_number`),
    INDEX `idx_friend_requests_sender_id` (`sender_id`),
    INDEX `idx_friend_requests_recipient_id` (`recipient_id`),
    INDEX `idx_friend_requests_status` (`status`),
    INDEX `idx_friend_requests_expires_at` (`expires_at`),
    FOREIGN KEY (`sender_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`recipient_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 好友关系表
CREATE TABLE IF NOT EXISTS `friendships` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id_1` CHAR(36) NOT NULL COMMENT '用户ID（较小者）',
    `user_id_2` CHAR(36) NOT NULL COMMENT '用户ID（较大者）',
    `request_id` CHAR(36) COMMENT '关联的好友申请ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_friendships_user_pair` (`user_id_1`, `user_id_2`),
    INDEX `idx_friendships_user_id_1` (`user_id_1`),
    INDEX `idx_friendships_user_id_2` (`user_id_2`),
    FOREIGN KEY (`user_id_1`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id_2`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`request_id`) REFERENCES `friend_requests`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户拉黑表
CREATE TABLE IF NOT EXISTS `user_blocks` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `blocker_id` CHAR(36) NOT NULL COMMENT '拉黑者用户ID',
    `blocked_id` CHAR(36) NOT NULL COMMENT '被拉黑者用户ID',
    `reason` VARCHAR(200) COMMENT '拉黑原因',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_user_blocks_blocker_blocked` (`blocker_id`, `blocked_id`),
    INDEX `idx_user_blocks_blocker_id` (`blocker_id`),
    INDEX `idx_user_blocks_blocked_id` (`blocked_id`),
    FOREIGN KEY (`blocker_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`blocked_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 会话表
CREATE TABLE IF NOT EXISTS `conversations` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `friendship_id` CHAR(36) COMMENT '好友关系ID',
    `user_id_1` CHAR(36) NOT NULL COMMENT '用户ID（较小者）',
    `user_id_2` CHAR(36) NOT NULL COMMENT '用户ID（较大者）',
    `last_message_at` DATETIME COMMENT '最后消息时间',
    `last_message_preview` VARCHAR(200) COMMENT '最后消息预览',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_conversations_user_pair` (`user_id_1`, `user_id_2`),
    INDEX `idx_conversations_user_id_1` (`user_id_1`),
    INDEX `idx_conversations_user_id_2` (`user_id_2`),
    INDEX `idx_conversations_last_message` (`last_message_at`),
    FOREIGN KEY (`friendship_id`) REFERENCES `friendships`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`user_id_1`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id_2`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 私聊消息表
CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `conversation_id` CHAR(36) NOT NULL COMMENT '会话ID',
    `sender_id` CHAR(36) NOT NULL COMMENT '发送者ID',
    `message_type` VARCHAR(20) DEFAULT 'text' COMMENT '消息类型：text/image/voice',
    `content` TEXT COMMENT '消息内容',
    `media_url` VARCHAR(500) COMMENT '媒体文件URL',
    `expires_at` DATETIME COMMENT '过期时间（图片消息90天后过期）',
    `is_read` TINYINT(1) DEFAULT 0 COMMENT '是否已读',
    `read_at` DATETIME COMMENT '已读时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_chat_messages_conversation` (`conversation_id`, `created_at` DESC),
    INDEX `idx_chat_messages_sender` (`sender_id`),
    INDEX `idx_chat_messages_expires` (`expires_at`),
    FOREIGN KEY (`conversation_id`) REFERENCES `conversations`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`sender_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 管理后台（必须在 AI 系统之前创建，ai_messages.crisis_resolved_by 引用 admins.id）
-- ============================================================

-- 管理员表
CREATE TABLE IF NOT EXISTS `admins` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `username` VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希（bcrypt）',
    `nickname` VARCHAR(50) COMMENT '昵称',
    `role` VARCHAR(20) DEFAULT 'admin' COMMENT '角色：super_admin/admin/operator',
    `permissions` JSON COMMENT '权限列表（JSON）',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `last_login_at` DATETIME COMMENT '最后登录时间',
    `last_login_ip` VARCHAR(45) COMMENT '最后登录IP',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_admins_username` (`username`),
    INDEX `idx_admins_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 操作日志表
CREATE TABLE IF NOT EXISTS `admin_logs` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `admin_id` CHAR(36) NOT NULL COMMENT '管理员ID',
    `action` VARCHAR(50) NOT NULL COMMENT '操作类型：login/logout/create/update/delete/export 等',
    `target_type` VARCHAR(50) COMMENT '操作对象类型：user/post/comment/report 等',
    `target_id` CHAR(36) COMMENT '操作对象ID',
    `details` JSON COMMENT '操作详情（JSON）',
    `ip_address` VARCHAR(45) COMMENT '操作IP',
    `user_agent` VARCHAR(500) COMMENT '浏览器User-Agent',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_admin_logs_admin` (`admin_id`),
    INDEX `idx_admin_logs_action` (`action`),
    INDEX `idx_admin_logs_target` (`target_type`, `target_id`),
    INDEX `idx_admin_logs_created` (`created_at` DESC),
    FOREIGN KEY (`admin_id`) REFERENCES `admins`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- AI 对话系统
-- ============================================================

-- AI对话会话表
CREATE TABLE IF NOT EXISTS `ai_conversations` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `ai_persona` VARCHAR(20) NOT NULL COMMENT 'AI人设：xiaowen/laohei/ali',
    `title` VARCHAR(100) COMMENT '会话标题',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否活跃',
    `last_message_at` DATETIME COMMENT '最后消息时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI对话消息表
CREATE TABLE IF NOT EXISTS `ai_messages` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `conversation_id` CHAR(36) NOT NULL COMMENT '会话ID',
    `role` VARCHAR(20) NOT NULL COMMENT '角色：user/assistant',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `token_count` INT COMMENT 'token 消耗数',
    `crisis_level` VARCHAR(10) COMMENT '危机级别：low/medium/high',
    `crisis_keywords` VARCHAR(200) COMMENT '匹配到的危机关键词（逗号分隔）',
    `crisis_status` VARCHAR(20) DEFAULT 'pending' COMMENT '危机状态：pending/intervening/resolved/false_positive',
    `crisis_resolved_by` CHAR(36) COMMENT '处理人ID',
    `crisis_resolution_note` TEXT COMMENT '处理备注',
    `crisis_resolved_at` DATETIME COMMENT '处理时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_ai_messages_conversation` (`conversation_id`, `created_at` DESC),
    FOREIGN KEY (`conversation_id`) REFERENCES `ai_conversations`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`crisis_resolved_by`) REFERENCES `admins`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI记忆表
CREATE TABLE IF NOT EXISTS `ai_memories` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `conversation_id` CHAR(36) COMMENT '来源会话ID',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `memory_type` VARCHAR(20) NOT NULL COMMENT '记忆类型：short_term/mid_term/long_term/person_info/event',
    `content` TEXT NOT NULL COMMENT '记忆内容',
    `key_facts` JSON COMMENT '关键事实（JSON）',
    `importance` INT DEFAULT 5 COMMENT '重要度 1~10',
    `source` VARCHAR(50) COMMENT '来源：chat/diary/behavior',
    `expires_at` DATETIME COMMENT '过期时间',
    `access_count` INT DEFAULT 0 COMMENT '被召回次数',
    `last_accessed_at` DATETIME COMMENT '最后被召回时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_ai_memories_user_type` (`user_id`, `memory_type`),
    INDEX `idx_ai_memories_conversation` (`conversation_id`),
    INDEX `idx_ai_memories_expires` (`expires_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`conversation_id`) REFERENCES `ai_conversations`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 通知系统
-- ============================================================

-- 通知推送表
CREATE TABLE IF NOT EXISTS `notifications` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `type` VARCHAR(30) NOT NULL COMMENT '通知类型：friend_request/message/system/ai_reply 等',
    `title` VARCHAR(100) NOT NULL COMMENT '通知标题',
    `content` TEXT COMMENT '通知内容',
    `payload` JSON COMMENT '附加数据（JSON）',
    `is_read` TINYINT(1) DEFAULT 0 COMMENT '是否已读',
    `read_at` DATETIME COMMENT '已读时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_notifications_user_unread` (`user_id`, `is_read`, `created_at` DESC),
    INDEX `idx_notifications_user_created` (`user_id`, `created_at` DESC),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 推送记录表（频率控制）
CREATE TABLE IF NOT EXISTS `push_records` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `notification_id` CHAR(36) COMMENT '关联通知ID',
    `push_type` VARCHAR(30) NOT NULL COMMENT '推送类型：system/reminder/marketing',
    `device_token` VARCHAR(200) COMMENT '设备推送Token',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/sent/failed',
    `sent_at` DATETIME COMMENT '发送时间',
    `error_message` VARCHAR(500) COMMENT '错误信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_push_records_user_type` (`user_id`, `push_type`, `sent_at` DESC),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`notification_id`) REFERENCES `notifications`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 举报系统
-- ============================================================

-- 举报记录表
CREATE TABLE IF NOT EXISTS `reports` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `reporter_id` CHAR(36) NOT NULL COMMENT '举报人ID',
    `reported_user_id` CHAR(36) COMMENT '被举报人ID',
    `reported_content_type` VARCHAR(30) NOT NULL COMMENT '举报内容类型：post/treehole_post/comment/user',
    `reported_content_id` CHAR(36) COMMENT '举报内容ID',
    `report_type` VARCHAR(30) NOT NULL COMMENT '举报分类：porn/ad/harassment/abuse/scam/self_harm/other',
    `reason` TEXT COMMENT '详细原因',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/processing/approved/rejected',
    `process_result` TEXT COMMENT '处理结果说明',
    `processed_by` CHAR(36) COMMENT '处理人管理员ID',
    `processed_at` DATETIME COMMENT '处理时间',
    `appeal_status` VARCHAR(20) COMMENT '申诉状态：pending/approved/rejected',
    `appeal_reason` TEXT COMMENT '申诉理由',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_reports_reporter_id` (`reporter_id`),
    INDEX `idx_reports_reported_user_id` (`reported_user_id`),
    INDEX `idx_reports_content` (`reported_content_type`, `reported_content_id`),
    INDEX `idx_reports_status` (`status`),
    INDEX `idx_reports_type` (`report_type`),
    INDEX `idx_reports_created` (`created_at`),
    FOREIGN KEY (`reporter_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`reported_user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`processed_by`) REFERENCES `admins`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 情绪周报系统
-- ============================================================

-- 情绪周报表
CREATE TABLE IF NOT EXISTS `weekly_reports` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `week_start_date` DATE NOT NULL COMMENT '本周起始日期（周一）',
    `title` VARCHAR(50) COMMENT '动态标题',
    `story_line` TEXT COMMENT '情绪故事线',
    `keywords` JSON COMMENT '情绪关键词列表',
    `insight` VARCHAR(100) COMMENT '一句看见',
    `suggestion` VARCHAR(200) COMMENT '温和建议',
    `outlook` VARCHAR(100) COMMENT '下周展望',
    `diary_count` INT DEFAULT 0 COMMENT '本周分析日记数量',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_weekly_reports_user_week` (`user_id`, `week_start_date`),
    INDEX `idx_weekly_reports_user_id` (`user_id`),
    INDEX `idx_weekly_reports_week_start` (`week_start_date`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 节日系统
-- ============================================================

-- 节日配置表（系统内置）
CREATE TABLE IF NOT EXISTS `holidays` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `name` VARCHAR(50) NOT NULL COMMENT '节日名称',
    `holiday_type` VARCHAR(20) NOT NULL COMMENT '类型：legal/traditional/special',
    `month` INT NOT NULL COMMENT '月份（1-12）',
    `day` INT NOT NULL COMMENT '日期（1-31）',
    `is_lunar` TINYINT(1) DEFAULT 0 COMMENT '是否农历',
    `description` TEXT COMMENT '节日描述',
    `greeting_template` VARCHAR(200) COMMENT '问候语模板，支持 {name} 占位符',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_holidays_date` (`month`, `day`),
    INDEX `idx_holidays_type` (`holiday_type`),
    INDEX `idx_holidays_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户自定义节日表
CREATE TABLE IF NOT EXISTS `user_holidays` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `name` VARCHAR(50) NOT NULL COMMENT '节日名称',
    `month` INT NOT NULL COMMENT '月份（1-12）',
    `day` INT NOT NULL COMMENT '日期（1-31）',
    `is_lunar` TINYINT(1) DEFAULT 0 COMMENT '是否农历',
    `year` INT COMMENT '年份（可选）',
    `reminder_enabled` TINYINT(1) DEFAULT 1 COMMENT '是否开启提醒',
    `reminder_time` VARCHAR(10) DEFAULT '10:00' COMMENT '提醒时间（HH:MM 格式）',
    `notes` VARCHAR(200) COMMENT '备注信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_user_holidays_user_date_name` (`user_id`, `month`, `day`, `name`),
    INDEX `idx_user_holidays_user_id` (`user_id`),
    INDEX `idx_user_holidays_date` (`month`, `day`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 处罚系统
-- ============================================================

-- 处罚记录表
CREATE TABLE IF NOT EXISTS `penalty_records` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '被处罚用户ID',
    `violation_type` VARCHAR(50) NOT NULL COMMENT '违规类型',
    `violation_severity` VARCHAR(20) NOT NULL COMMENT '违规程度：minor/moderate/severe',
    `penalty_type` VARCHAR(30) NOT NULL COMMENT '处罚类型',
    `penalty_count` INT DEFAULT 1 NOT NULL COMMENT '该违规类型的累计次数',
    `reason` VARCHAR(500) COMMENT '处罚原因描述',
    `evidence` TEXT COMMENT '证据（JSON格式）',
    `expires_at` DATETIME COMMENT '处罚结束时间（null表示永久）',
    `is_active` TINYINT(1) DEFAULT 1 NOT NULL COMMENT '处罚是否生效中',
    `appeal_status` VARCHAR(20) COMMENT '申诉状态：pending/approved/rejected',
    `appeal_reason` VARCHAR(500) COMMENT '申诉理由',
    `reviewed_by` CHAR(36) COMMENT '审核管理员ID',
    `reviewed_at` DATETIME COMMENT '审核时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_penalty_records_user_id` (`user_id`),
    INDEX `idx_penalty_records_violation_type` (`violation_type`),
    INDEX `idx_penalty_records_is_active` (`is_active`),
    INDEX `idx_penalty_records_created` (`created_at`),
    INDEX `idx_penalty_records_appeal_status` (`appeal_status`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 设备封禁表
CREATE TABLE IF NOT EXISTS `device_bans` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `device_fingerprint` VARCHAR(128) UNIQUE NOT NULL COMMENT '设备指纹',
    `user_id` CHAR(36) COMMENT '关联用户ID',
    `ban_reason` VARCHAR(500) NOT NULL COMMENT '封禁原因',
    `related_penalty_id` CHAR(36) COMMENT '关联的处罚记录ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_device_bans_fingerprint` (`device_fingerprint`),
    INDEX `idx_device_bans_user_id` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`related_penalty_id`) REFERENCES `penalty_records`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 用户行为事件
-- ============================================================

-- 用户行为事件表
CREATE TABLE IF NOT EXISTS `user_events` (
    `id` CHAR(36) PRIMARY KEY COMMENT '主键UUID，应用层生成',
    `user_id` CHAR(36) NOT NULL COMMENT '用户ID',
    `event_type` VARCHAR(50) NOT NULL COMMENT '事件类型：diary_created/ai_chat_message/friend_request_sent 等',
    `event_data` JSON COMMENT '事件附加数据（JSON）',
    `source` VARCHAR(20) COMMENT '事件来源：app/web/mini_program',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_user_events_user_id` (`user_id`),
    INDEX `idx_user_events_event_type` (`event_type`),
    INDEX `idx_user_events_user_type` (`user_id`, `event_type`),
    INDEX `idx_user_events_created_at` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- NPS 评分
-- ============================================================

-- NPS 评分记录表
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
-- 初始化完成
-- ============================================================

SELECT 'echo_meet 数据库初始化完成（与 SQLAlchemy 模型完全对齐）' AS status;
