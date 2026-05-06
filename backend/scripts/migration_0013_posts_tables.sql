-- ============================================================
-- 数据库迁移脚本：0013_posts_tables
-- 日期：2026-05-06
--
-- 补充内容：
-- 1. posts 表添加 anon_identity_id 和 favorite_count 字段
-- 2. 创建 post_comments 表
-- 3. 创建 post_likes 表
-- 4. 创建 post_favorites 表
-- 5. 创建 post_follows 表
-- ============================================================

-- ==================== 1. posts 表添加字段 ====================

-- 添加 anon_identity_id 字段
ALTER TABLE posts ADD COLUMN anon_identity_id CHAR(36) NULL COMMENT '匿名身份ID（匿名发布时使用）' AFTER is_anonymous;
ALTER TABLE posts ADD CONSTRAINT fk_posts_anon_identity_id FOREIGN KEY (anon_identity_id) REFERENCES anonymous_identities(id) ON DELETE SET NULL;
CREATE INDEX idx_posts_anon_identity_id ON posts(anon_identity_id);

-- 添加 favorite_count 字段
ALTER TABLE posts ADD COLUMN favorite_count INT DEFAULT 0 COMMENT '收藏数' AFTER like_count;

-- ==================== 2. post_comments 评论表 ====================

CREATE TABLE post_comments (
    id CHAR(36) PRIMARY KEY COMMENT '主键UUID',
    post_id CHAR(36) NOT NULL COMMENT '动态ID',
    user_id CHAR(36) NOT NULL COMMENT '用户ID',
    anon_identity_id CHAR(36) NULL COMMENT '匿名身份ID（匿名评论时使用）',
    content VARCHAR(500) NOT NULL COMMENT '评论内容，最多500字',
    is_anonymous BOOLEAN DEFAULT FALSE COMMENT '是否匿名评论',
    reply_to_comment_id CHAR(36) NULL COMMENT '回复的评论ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    deleted_at DATETIME NULL COMMENT '删除时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_post_comments_post_id FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_comments_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_comments_anon_identity FOREIGN KEY (anon_identity_id) REFERENCES anonymous_identities(id) ON DELETE SET NULL,
    CONSTRAINT fk_post_comments_reply_to FOREIGN KEY (reply_to_comment_id) REFERENCES post_comments(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态评论表';

CREATE INDEX idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX idx_post_comments_user_id ON post_comments(user_id);
CREATE INDEX idx_post_comments_created ON post_comments(created_at);

-- ==================== 3. post_likes 点赞表 ====================

CREATE TABLE post_likes (
    id CHAR(36) PRIMARY KEY COMMENT '主键UUID',
    post_id CHAR(36) NOT NULL COMMENT '动态ID',
    user_id CHAR(36) NOT NULL COMMENT '用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_post_likes_post_id FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_likes_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_post_likes_post_user UNIQUE (post_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态点赞表';

CREATE INDEX idx_post_likes_post_id ON post_likes(post_id);
CREATE INDEX idx_post_likes_user_id ON post_likes(user_id);

-- ==================== 4. post_favorites 收藏表 ====================

CREATE TABLE post_favorites (
    id CHAR(36) PRIMARY KEY COMMENT '主键UUID',
    post_id CHAR(36) NOT NULL COMMENT '动态ID',
    user_id CHAR(36) NOT NULL COMMENT '用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_post_favorites_post_id FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_favorites_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_post_favorites_post_user UNIQUE (post_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态收藏表';

CREATE INDEX idx_post_favorites_user_id ON post_favorites(user_id);

-- ==================== 5. post_follows 关注表 ====================

CREATE TABLE post_follows (
    id CHAR(36) PRIMARY KEY COMMENT '主键UUID',
    post_id CHAR(36) NOT NULL COMMENT '动态ID',
    follower_id CHAR(36) NOT NULL COMMENT '关注者ID',
    following_id CHAR(36) NOT NULL COMMENT '被关注者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_post_follows_post_id FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_follows_follower FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_follows_following FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_post_follows_follower_following UNIQUE (follower_id, following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态关注表';

CREATE INDEX idx_post_follows_follower_id ON post_follows(follower_id);
CREATE INDEX idx_post_follows_following_id ON post_follows(following_id);

-- ==================== 6. 更新 alembic 版本 ====================

INSERT INTO alembic_version (version_num) VALUES ('0013');

-- ==================== 验证 ====================

-- 验证 posts 表字段
SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'posts' AND COLUMN_NAME IN ('anon_identity_id', 'favorite_count');

-- 验证新表
SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name IN ('post_comments', 'post_likes', 'post_favorites', 'post_follows');