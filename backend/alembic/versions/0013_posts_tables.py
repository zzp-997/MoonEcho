"""补充动态广场缺失的表和字段

Revision ID: 0013
Revises: 0012_nps_records
Create Date: 2026-05-06

补充内容：
1. posts 表添加 anon_identity_id 和 favorite_count 字段
2. 创建 post_comments 表
3. 创建 post_likes 表
4. 创建 post_favorites 表
5. 创建 post_follows 表

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, None] = "0012_nps_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------
    # 1. posts 表添加缺失字段
    # ----------------------------------------------------------
    # 检查字段是否存在，避免重复添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    posts_columns = [col['name'] for col in inspector.get_columns('posts')]

    if 'anon_identity_id' not in posts_columns:
        op.add_column(
            "posts",
            sa.Column(
                "anon_identity_id",
                sa.CHAR(36),
                sa.ForeignKey("anonymous_identities.id", ondelete="SET NULL"),
                nullable=True,
                comment="匿名身份ID（匿名发布时使用）",
            ),
        )
        op.create_index("idx_posts_anon_identity_id", "posts", ["anon_identity_id"])

    if 'favorite_count' not in posts_columns:
        op.add_column(
            "posts",
            sa.Column(
                "favorite_count",
                sa.Integer,
                default=0,
                server_default="0",
                comment="收藏数",
            ),
        )

    # ----------------------------------------------------------
    # 2. post_comments — 动态评论表
    # ----------------------------------------------------------
    if not inspector.has_table("post_comments"):
        op.create_table(
            "post_comments",
            sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
            sa.Column(
                "post_id",
                sa.CHAR(36),
                sa.ForeignKey("posts.id", ondelete="CASCADE"),
                nullable=False,
                comment="动态ID",
            ),
            sa.Column(
                "user_id",
                sa.CHAR(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="用户ID",
            ),
            sa.Column(
                "anon_identity_id",
                sa.CHAR(36),
                sa.ForeignKey("anonymous_identities.id", ondelete="SET NULL"),
                nullable=True,
                comment="匿名身份ID（匿名评论时使用）",
            ),
            sa.Column(
                "content",
                sa.String(500),
                nullable=False,
                comment="评论内容，最多500字",
            ),
            sa.Column(
                "is_anonymous",
                sa.Boolean,
                default=False,
                server_default="0",
                comment="是否匿名评论",
            ),
            sa.Column(
                "reply_to_comment_id",
                sa.CHAR(36),
                sa.ForeignKey("post_comments.id", ondelete="SET NULL"),
                nullable=True,
                comment="回复的评论ID",
            ),
            sa.Column(
                "is_active",
                sa.Boolean,
                default=True,
                server_default="1",
                comment="是否有效",
            ),
            sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
            sa.Column(
                "created_at",
                sa.DateTime,
                server_default=sa.func.now(),
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="更新时间",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_post_comments_post_id", "post_comments", ["post_id"])
        op.create_index("idx_post_comments_user_id", "post_comments", ["user_id"])
        op.create_index("idx_post_comments_created", "post_comments", ["created_at"])

    # ----------------------------------------------------------
    # 3. post_likes — 动态共鸣（点赞）记录表
    # ----------------------------------------------------------
    if not inspector.has_table("post_likes"):
        op.create_table(
            "post_likes",
            sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
            sa.Column(
                "post_id",
                sa.CHAR(36),
                sa.ForeignKey("posts.id", ondelete="CASCADE"),
                nullable=False,
                comment="动态ID",
            ),
            sa.Column(
                "user_id",
                sa.CHAR(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="用户ID",
            ),
            sa.Column(
                "created_at",
                sa.DateTime,
                server_default=sa.func.now(),
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="更新时间",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("post_id", "user_id", name="uk_post_likes_post_user"),
        )
        op.create_index("idx_post_likes_post_id", "post_likes", ["post_id"])
        op.create_index("idx_post_likes_user_id", "post_likes", ["user_id"])

    # ----------------------------------------------------------
    # 4. post_favorites — 动态收藏记录表
    # ----------------------------------------------------------
    if not inspector.has_table("post_favorites"):
        op.create_table(
            "post_favorites",
            sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
            sa.Column(
                "post_id",
                sa.CHAR(36),
                sa.ForeignKey("posts.id", ondelete="CASCADE"),
                nullable=False,
                comment="动态ID",
            ),
            sa.Column(
                "user_id",
                sa.CHAR(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="用户ID",
            ),
            sa.Column(
                "created_at",
                sa.DateTime,
                server_default=sa.func.now(),
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="更新时间",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("post_id", "user_id", name="uk_post_favorites_post_user"),
        )
        op.create_index("idx_post_favorites_user_id", "post_favorites", ["user_id"])

    # ----------------------------------------------------------
    # 5. post_follows — 动态悄悄关注记录表
    # ----------------------------------------------------------
    if not inspector.has_table("post_follows"):
        op.create_table(
            "post_follows",
            sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
            sa.Column(
                "post_id",
                sa.CHAR(36),
                sa.ForeignKey("posts.id", ondelete="CASCADE"),
                nullable=False,
                comment="动态ID",
            ),
            sa.Column(
                "follower_id",
                sa.CHAR(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="关注者ID",
            ),
            sa.Column(
                "following_id",
                sa.CHAR(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="被关注者ID",
            ),
            sa.Column(
                "created_at",
                sa.DateTime,
                server_default=sa.func.now(),
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="更新时间",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "follower_id", "following_id", name="uk_post_follows_follower_following"
            ),
        )
        op.create_index("idx_post_follows_follower_id", "post_follows", ["follower_id"])
        op.create_index("idx_post_follows_following_id", "post_follows", ["following_id"])


def downgrade() -> None:
    # 删除表
    op.drop_table("post_follows")
    op.drop_table("post_favorites")
    op.drop_table("post_likes")
    op.drop_table("post_comments")

    # 删除 posts 表新增的字段
    op.drop_column("posts", "favorite_count")
    op.drop_index("idx_posts_anon_identity_id", "posts")
    op.drop_column("posts", "anon_identity_id")
