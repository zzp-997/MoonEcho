"""初始数据库结构

Revision ID: 0001_initial
Revises: None
Create Date: 2026-04-25

创建所有核心表结构，包括：
- 用户系统（users, user_tags, anonymous_identities, user_anon_mapping）
- 情绪日记（emotion_diaries）
- 树洞系统（treehole_posts, treehole_comments）
- 动态广场（posts）
- 聊天系统（friendships, conversations, chat_messages）
- AI 对话系统（ai_conversations, ai_messages, ai_memories）
- 通知系统（notifications, push_records）
- 管理后台（admins, admin_logs）
- 举报系统（reports）

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建所有表结构。"""

    # ----------------------------------------------------------
    # users — 用户表
    # ----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("phone", sa.String(20), unique=True, nullable=False, comment="手机号"),
        sa.Column("phone_hash", sa.String(64), unique=True, nullable=False, comment="手机号哈希"),
        sa.Column("nickname", sa.String(50), comment="昵称"),
        sa.Column("avatar_url", sa.String(500), comment="头像URL"),
        sa.Column("age_range", sa.String(10), comment="年龄段"),
        sa.Column("city", sa.String(50), comment="所在城市"),
        sa.Column("occupation", sa.String(50), comment="职业"),
        sa.Column("notification_settings", sa.JSON, comment="通知偏好设置"),
        sa.Column("is_minor", sa.Boolean, default=False, server_default="0", comment="是否未成年人"),
        sa.Column("social_energy", sa.DECIMAL(5, 2), comment="社交能量值"),
        sa.Column("social_energy_updated_at", sa.DateTime, comment="社交能量最后更新时间"),
        sa.Column("last_active_at", sa.DateTime, comment="最后活跃时间"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_users_phone_hash", "users", ["phone_hash"])
    op.create_index("idx_users_created", "users", ["created_at"])
    op.create_index("idx_users_last_active", "users", ["last_active_at"])
    op.create_index("idx_users_is_active", "users", ["is_active"])

    # ----------------------------------------------------------
    # user_tags — 用户画像标签表
    # ----------------------------------------------------------
    op.create_table(
        "user_tags",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("tag_key", sa.String(50), nullable=False, comment="标签键"),
        sa.Column("tag_value", sa.String(100), nullable=False, comment="标签值"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tag_key", name="uk_user_tags_user_tag_key"),
    )
    op.create_index("idx_user_tags_user_id", "user_tags", ["user_id"])
    op.create_index("idx_user_tags_tag_key", "user_tags", ["tag_key"])

    # ----------------------------------------------------------
    # anonymous_identities — 匿名身份表
    # ----------------------------------------------------------
    op.create_table(
        "anonymous_identities",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("anon_nickname", sa.String(50), nullable=False, comment="匿名昵称"),
        sa.Column("anon_avatar_url", sa.String(500), comment="匿名头像URL"),
        sa.Column("persona_type", sa.String(30), comment="人设类型"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_anon_identities_user_id", "anonymous_identities", ["user_id"])

    # ----------------------------------------------------------
    # user_anon_mapping — 用户-匿名身份映射表
    # ----------------------------------------------------------
    op.create_table(
        "user_anon_mapping",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("anon_identity_id", sa.CHAR(36), sa.ForeignKey("anonymous_identities.id", ondelete="CASCADE"), nullable=False, comment="匿名身份ID"),
        sa.Column("scene", sa.String(30), nullable=False, comment="使用场景"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "scene", name="uk_user_anon_mapping_user_scene"),
    )
    op.create_index("idx_user_anon_mapping_user_id", "user_anon_mapping", ["user_id"])
    op.create_index("idx_user_anon_mapping_anon_id", "user_anon_mapping", ["anon_identity_id"])

    # ----------------------------------------------------------
    # emotion_diaries — 情绪日记表
    # ----------------------------------------------------------
    op.create_table(
        "emotion_diaries",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("emotion_tone", sa.String(30), comment="情绪基调"),
        sa.Column("emotion_labels", sa.JSON, comment="情绪标签列表"),
        sa.Column("content_text", sa.Text, comment="日记内容"),
        sa.Column("content_hash", sa.String(64), comment="内容哈希"),
        sa.Column("record_date", sa.Date, nullable=False, comment="记录日期"),
        sa.Column("is_synced", sa.Boolean, default=False, server_default="0", comment="是否已同步"),
        sa.Column("client_id", sa.String(50), comment="客户端唯一标识"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "record_date", "client_id", name="uk_emotion_diaries_user_date_client"),
    )
    op.create_index("idx_emotion_diaries_user_id", "emotion_diaries", ["user_id"])
    op.create_index("idx_emotion_diaries_record_date", "emotion_diaries", ["record_date"])
    op.create_index("idx_emotion_diaries_user_date", "emotion_diaries", ["user_id", "record_date"])

    # ----------------------------------------------------------
    # treehole_posts — 树洞吐槽表
    # ----------------------------------------------------------
    op.create_table(
        "treehole_posts",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("anon_identity_id", sa.CHAR(36), sa.ForeignKey("anonymous_identities.id", ondelete="SET NULL"), comment="匿名身份ID"),
        sa.Column("content", sa.Text, nullable=False, comment="帖子内容"),
        sa.Column("topic_tag", sa.String(50), comment="话题标签"),
        sa.Column("image_urls", sa.JSON, comment="图片URL列表"),
        sa.Column("resonance_count", sa.Integer, default=0, server_default="0", comment="共鸣数"),
        sa.Column("comment_count", sa.Integer, default=0, server_default="0", comment="评论数"),
        sa.Column("status", sa.String(20), default="active", server_default="active", comment="状态"),
        sa.Column("expires_at", sa.DateTime, comment="过期时间"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_treehole_posts_user_id", "treehole_posts", ["user_id"])
    op.create_index("idx_treehole_posts_anon_id", "treehole_posts", ["anon_identity_id"])
    op.create_index("idx_treehole_posts_status", "treehole_posts", ["status"])
    op.create_index("idx_treehole_posts_created", "treehole_posts", ["created_at"])
    op.create_index("idx_treehole_posts_topic", "treehole_posts", ["topic_tag"])

    # ----------------------------------------------------------
    # treehole_comments — 树洞评论表
    # ----------------------------------------------------------
    op.create_table(
        "treehole_comments",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("post_id", sa.CHAR(36), sa.ForeignKey("treehole_posts.id", ondelete="CASCADE"), nullable=False, comment="帖子ID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("content", sa.String(100), nullable=False, comment="评论内容"),
        sa.Column("is_resonance", sa.Boolean, default=False, server_default="0", comment="是否为共鸣"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_treehole_comments_post_id", "treehole_comments", ["post_id"])
    op.create_index("idx_treehole_comments_user_id", "treehole_comments", ["user_id"])
    op.create_index("idx_treehole_comments_created", "treehole_comments", ["created_at"])

    # ----------------------------------------------------------
    # posts — 动态广场表
    # ----------------------------------------------------------
    op.create_table(
        "posts",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("content", sa.Text, nullable=False, comment="动态内容"),
        sa.Column("image_urls", sa.JSON, comment="图片URL列表"),
        sa.Column("is_anonymous", sa.Boolean, default=False, server_default="0", comment="是否匿名发布"),
        sa.Column("visibility", sa.String(20), default="public", server_default="public", comment="可见性"),
        sa.Column("like_count", sa.Integer, default=0, server_default="0", comment="点赞数"),
        sa.Column("comment_count", sa.Integer, default=0, server_default="0", comment="评论数"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_posts_user_id", "posts", ["user_id"])
    op.create_index("idx_posts_created", "posts", ["created_at"])
    op.create_index("idx_posts_visibility", "posts", ["visibility"])
    op.create_index("idx_posts_is_active", "posts", ["is_active"])

    # ----------------------------------------------------------
    # friendships — 好友关系表
    # ----------------------------------------------------------
    op.create_table(
        "friendships",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id_1", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较小者）"),
        sa.Column("user_id_2", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较大者）"),
        sa.Column("initiator_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="发起方用户ID"),
        sa.Column("status", sa.String(20), default="pending", server_default="pending", comment="状态"),
        sa.Column("greeting_message", sa.String(200), comment="好友申请附言"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id_1", "user_id_2", name="uk_friendships_user_pair"),
    )
    op.create_index("idx_friendships_user_id_1", "friendships", ["user_id_1"])
    op.create_index("idx_friendships_user_id_2", "friendships", ["user_id_2"])
    op.create_index("idx_friendships_status", "friendships", ["status"])
    op.create_index("idx_friendships_initiator", "friendships", ["initiator_id"])

    # ----------------------------------------------------------
    # conversations — 会话表
    # ----------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("friendship_id", sa.CHAR(36), sa.ForeignKey("friendships.id", ondelete="SET NULL"), comment="好友关系ID"),
        sa.Column("user_id_1", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较小者）"),
        sa.Column("user_id_2", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较大者）"),
        sa.Column("last_message_at", sa.DateTime, comment="最后消息时间"),
        sa.Column("last_message_preview", sa.String(200), comment="最后消息预览"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id_1", "user_id_2", name="uk_conversations_user_pair"),
    )
    op.create_index("idx_conversations_user_id_1", "conversations", ["user_id_1"])
    op.create_index("idx_conversations_user_id_2", "conversations", ["user_id_2"])
    op.create_index("idx_conversations_last_message", "conversations", ["last_message_at"])

    # ----------------------------------------------------------
    # chat_messages — 私聊消息表
    # ----------------------------------------------------------
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("conversation_id", sa.CHAR(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="会话ID"),
        sa.Column("sender_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="发送者ID"),
        sa.Column("message_type", sa.String(20), default="text", server_default="text", comment="消息类型"),
        sa.Column("content", sa.Text, comment="消息内容"),
        sa.Column("media_url", sa.String(500), comment="媒体文件URL"),
        sa.Column("is_read", sa.Boolean, default=False, server_default="0", comment="是否已读"),
        sa.Column("read_at", sa.DateTime, comment="已读时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chat_messages_conversation_id", "chat_messages", ["conversation_id"])
    op.create_index("idx_chat_messages_sender_id", "chat_messages", ["sender_id"])
    op.create_index("idx_chat_messages_created", "chat_messages", ["created_at"])

    # ----------------------------------------------------------
    # ai_conversations — AI对话会话表
    # ----------------------------------------------------------
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("ai_persona", sa.String(20), nullable=False, comment="AI人设"),
        sa.Column("title", sa.String(100), comment="会话标题"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否活跃"),
        sa.Column("last_message_at", sa.DateTime, comment="最后消息时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_conversations_user_id", "ai_conversations", ["user_id"])
    op.create_index("idx_ai_conversations_persona", "ai_conversations", ["ai_persona"])
    op.create_index("idx_ai_conversations_active", "ai_conversations", ["is_active"])

    # ----------------------------------------------------------
    # ai_messages — AI对话消息表
    # ----------------------------------------------------------
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("conversation_id", sa.CHAR(36), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, comment="会话ID"),
        sa.Column("role", sa.String(20), nullable=False, comment="角色"),
        sa.Column("content", sa.Text, nullable=False, comment="消息内容"),
        sa.Column("token_count", sa.Integer, comment="token消耗数"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_messages_conversation_id", "ai_messages", ["conversation_id"])
    op.create_index("idx_ai_messages_created", "ai_messages", ["created_at"])

    # ----------------------------------------------------------
    # ai_memories — AI记忆表
    # ----------------------------------------------------------
    op.create_table(
        "ai_memories",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("conversation_id", sa.CHAR(36), sa.ForeignKey("ai_conversations.id", ondelete="SET NULL"), comment="来源会话ID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("memory_type", sa.String(20), nullable=False, comment="记忆类型"),
        sa.Column("content", sa.Text, nullable=False, comment="记忆内容"),
        sa.Column("key_facts", sa.JSON, comment="关键事实"),
        sa.Column("importance", sa.Integer, default=5, server_default="5", comment="重要度"),
        sa.Column("source", sa.String(50), comment="来源"),
        sa.Column("expires_at", sa.DateTime, comment="过期时间"),
        sa.Column("access_count", sa.Integer, default=0, server_default="0", comment="被召回次数"),
        sa.Column("last_accessed_at", sa.DateTime, comment="最后被召回时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_memories_user_id", "ai_memories", ["user_id"])
    op.create_index("idx_ai_memories_conversation_id", "ai_memories", ["conversation_id"])
    op.create_index("idx_ai_memories_type", "ai_memories", ["memory_type"])
    op.create_index("idx_ai_memories_importance", "ai_memories", ["importance"])
    op.create_index("idx_ai_memories_expires", "ai_memories", ["expires_at"])

    # ----------------------------------------------------------
    # notifications — 通知推送表
    # ----------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("type", sa.String(30), nullable=False, comment="通知类型"),
        sa.Column("title", sa.String(100), nullable=False, comment="通知标题"),
        sa.Column("content", sa.Text, comment="通知内容"),
        sa.Column("payload", sa.JSON, comment="附加数据"),
        sa.Column("is_read", sa.Boolean, default=False, server_default="0", comment="是否已读"),
        sa.Column("read_at", sa.DateTime, comment="已读时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_type", "notifications", ["type"])
    op.create_index("idx_notifications_is_read", "notifications", ["is_read"])
    op.create_index("idx_notifications_created", "notifications", ["created_at"])

    # ----------------------------------------------------------
    # push_records — 推送记录表
    # ----------------------------------------------------------
    op.create_table(
        "push_records",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("notification_id", sa.CHAR(36), sa.ForeignKey("notifications.id", ondelete="SET NULL"), comment="关联通知ID"),
        sa.Column("push_type", sa.String(30), nullable=False, comment="推送类型"),
        sa.Column("device_token", sa.String(200), comment="设备推送Token"),
        sa.Column("status", sa.String(20), default="pending", server_default="pending", comment="状态"),
        sa.Column("sent_at", sa.DateTime, comment="发送时间"),
        sa.Column("error_message", sa.String(500), comment="错误信息"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_push_records_user_id", "push_records", ["user_id"])
    op.create_index("idx_push_records_notification_id", "push_records", ["notification_id"])
    op.create_index("idx_push_records_status", "push_records", ["status"])
    op.create_index("idx_push_records_created", "push_records", ["created_at"])

    # ----------------------------------------------------------
    # admins — 管理员表
    # ----------------------------------------------------------
    op.create_table(
        "admins",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("username", sa.String(50), unique=True, nullable=False, comment="用户名"),
        sa.Column("password_hash", sa.String(255), nullable=False, comment="密码哈希"),
        sa.Column("nickname", sa.String(50), comment="昵称"),
        sa.Column("role", sa.String(20), default="admin", server_default="admin", comment="角色"),
        sa.Column("permissions", sa.JSON, comment="权限列表"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否启用"),
        sa.Column("last_login_at", sa.DateTime, comment="最后登录时间"),
        sa.Column("last_login_ip", sa.String(45), comment="最后登录IP"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_admins_username", "admins", ["username"])
    op.create_index("idx_admins_role", "admins", ["role"])
    op.create_index("idx_admins_is_active", "admins", ["is_active"])

    # ----------------------------------------------------------
    # admin_logs — 操作日志表
    # ----------------------------------------------------------
    op.create_table(
        "admin_logs",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("admin_id", sa.CHAR(36), sa.ForeignKey("admins.id", ondelete="CASCADE"), nullable=False, comment="管理员ID"),
        sa.Column("action", sa.String(50), nullable=False, comment="操作类型"),
        sa.Column("target_type", sa.String(50), comment="操作对象类型"),
        sa.Column("target_id", sa.CHAR(36), comment="操作对象ID"),
        sa.Column("details", sa.JSON, comment="操作详情"),
        sa.Column("ip_address", sa.String(45), comment="操作IP"),
        sa.Column("user_agent", sa.String(500), comment="浏览器UA"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_admin_logs_admin_id", "admin_logs", ["admin_id"])
    op.create_index("idx_admin_logs_action", "admin_logs", ["action"])
    op.create_index("idx_admin_logs_target", "admin_logs", ["target_type", "target_id"])
    op.create_index("idx_admin_logs_created", "admin_logs", ["created_at"])

    # ----------------------------------------------------------
    # reports — 举报记录表
    # ----------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("reporter_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="举报人ID"),
        sa.Column("reported_user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="SET NULL"), comment="被举报人ID"),
        sa.Column("reported_content_type", sa.String(30), nullable=False, comment="举报内容类型"),
        sa.Column("reported_content_id", sa.CHAR(36), comment="举报内容ID"),
        sa.Column("report_type", sa.String(30), nullable=False, comment="举报分类"),
        sa.Column("reason", sa.Text, comment="详细原因"),
        sa.Column("status", sa.String(20), default="pending", server_default="pending", comment="状态"),
        sa.Column("process_result", sa.Text, comment="处理结果说明"),
        sa.Column("processed_by", sa.CHAR(36), sa.ForeignKey("admins.id", ondelete="SET NULL"), comment="处理人ID"),
        sa.Column("processed_at", sa.DateTime, comment="处理时间"),
        sa.Column("appeal_status", sa.String(20), comment="申诉状态"),
        sa.Column("appeal_reason", sa.Text, comment="申诉理由"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("idx_reports_reported_user_id", "reports", ["reported_user_id"])
    op.create_index("idx_reports_content", "reports", ["reported_content_type", "reported_content_id"])
    op.create_index("idx_reports_status", "reports", ["status"])
    op.create_index("idx_reports_type", "reports", ["report_type"])
    op.create_index("idx_reports_created", "reports", ["created_at"])


def downgrade() -> None:
    """删除所有表结构。"""
    # 按照依赖关系反向删除
    op.drop_table("reports")
    op.drop_table("admin_logs")
    op.drop_table("admins")
    op.drop_table("push_records")
    op.drop_table("notifications")
    op.drop_table("ai_memories")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
    op.drop_table("chat_messages")
    op.drop_table("conversations")
    op.drop_table("friendships")
    op.drop_table("posts")
    op.drop_table("treehole_comments")
    op.drop_table("treehole_posts")
    op.drop_table("emotion_diaries")
    op.drop_table("user_anon_mapping")
    op.drop_table("anonymous_identities")
    op.drop_table("user_tags")
    op.drop_table("users")
