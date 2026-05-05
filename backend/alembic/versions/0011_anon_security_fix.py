"""T025-B 安全架构修复：匿名身份加密存储

修复 PRD 7.5 匿名身份架构隔离缺陷：
1. TreeholePost: user_id → encrypted_user_id（加密存储）
2. TreeholeComment: user_id → anon_identity_id（完全匿名化）
3. AnonymousIdentity: user_id → encrypted_user_id（加密存储）
4. UserAnonMapping: 添加 user_id_hash（哈希查询）+ encrypted_user_id（加密存储）

Revision ID: 0011_anon_security_fix
Revises: 0010_penalty_records
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "0011_anon_security_fix"
down_revision = "0010_user_boundary_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库架构：实现匿名身份加密存储。"""

    # 1. 修改 treehole_posts 表
    # 添加 encrypted_user_id 字段
    op.add_column(
        "treehole_posts",
        sa.Column("encrypted_user_id", sa.String(200), nullable=True, comment="加密的用户ID（AES-256-GCM）"),
    )
    # 创建索引
    op.create_index(
        "idx_treehole_posts_encrypted_user_id",
        "treehole_posts",
        ["encrypted_user_id"],
    )

    # 2. 修改 treehole_comments 表
    # 添加 anon_identity_id 字段
    op.add_column(
        "treehole_comments",
        sa.Column("anon_identity_id", sa.CHAR(36), nullable=True, comment="匿名身份ID"),
    )
    # 添加外键约束
    op.create_foreign_key(
        "fk_treehole_comments_anon_identity_id",
        "treehole_comments",
        "anonymous_identities",
        ["anon_identity_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # 创建索引
    op.create_index(
        "idx_treehole_comments_anon_id",
        "treehole_comments",
        ["anon_identity_id"],
    )

    # 3. 修改 anonymous_identities 表
    # 添加 encrypted_user_id 字段
    op.add_column(
        "anonymous_identities",
        sa.Column("encrypted_user_id", sa.String(200), nullable=True, comment="加密的用户ID（AES-256-GCM）"),
    )
    # 创建索引
    op.create_index(
        "idx_anon_identities_encrypted_user_id",
        "anonymous_identities",
        ["encrypted_user_id"],
    )

    # 4. 修改 user_anon_mapping 表
    # 添加 user_id_hash 和 encrypted_user_id 字段
    op.add_column(
        "user_anon_mapping",
        sa.Column("user_id_hash", sa.String(64), nullable=True, comment="用户ID哈希（加盐SHA-256）"),
    )
    op.add_column(
        "user_anon_mapping",
        sa.Column("encrypted_user_id", sa.String(200), nullable=True, comment="加密的用户ID（AES-256-GCM）"),
    )
    # 创建唯一约束和索引
    op.create_unique_constraint(
        "uk_user_anon_mapping_user_scene",
        "user_anon_mapping",
        ["user_id_hash", "scene"],
    )
    op.create_index(
        "idx_user_anon_mapping_user_id_hash",
        "user_anon_mapping",
        ["user_id_hash"],
    )

    # 注意：数据迁移需要在应用层完成
    # 旧数据中的 user_id 需要加密后存入新字段
    # 建议在服务启动时检测并迁移数据


def downgrade() -> None:
    """回滚数据库架构变更。"""

    # 4. 回滚 user_anon_mapping 表
    op.drop_index("idx_user_anon_mapping_user_id_hash", "user_anon_mapping")
    op.drop_constraint("uk_user_anon_mapping_user_scene", "user_anon_mapping", type_="unique")
    op.drop_column("user_anon_mapping", "encrypted_user_id")
    op.drop_column("user_anon_mapping", "user_id_hash")

    # 3. 回滚 anonymous_identities 表
    op.drop_index("idx_anon_identities_encrypted_user_id", "anonymous_identities")
    op.drop_column("anonymous_identities", "encrypted_user_id")

    # 2. 回滚 treehole_comments 表
    op.drop_index("idx_treehole_comments_anon_id", "treehole_comments")
    op.drop_constraint("fk_treehole_comments_anon_identity_id", "treehole_comments", type_="foreignkey")
    op.drop_column("treehole_comments", "anon_identity_id")

    # 1. 回滚 treehole_posts 表
    op.drop_index("idx_treehole_posts_encrypted_user_id", "treehole_posts")
    op.drop_column("treehole_posts", "encrypted_user_id")
