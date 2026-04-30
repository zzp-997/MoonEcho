"""创建处罚记录表和设备封禁表。

Revision ID: 0010
Revises: 0009_chat_message_expires_at
Create Date: 2026-04-29

为 T025-A 安全审核系统增加处罚梯度机制支持。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, None] = "0009_chat_message_expires_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级到处罚表新版本。"""
    # 创建处罚记录表
    op.create_table(
        "penalty_records",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("violation_type", sa.String(50), nullable=False),
        sa.Column("violation_severity", sa.String(20), nullable=False),
        sa.Column("penalty_type", sa.String(30), nullable=False),
        sa.Column("penalty_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("appeal_status", sa.String(20), nullable=True),
        sa.Column("appeal_reason", sa.String(500), nullable=True),
        sa.Column("reviewed_by", sa.CHAR(36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index("idx_penalty_records_user_id", "penalty_records", ["user_id"])
    op.create_index("idx_penalty_records_violation_type", "penalty_records", ["violation_type"])
    op.create_index("idx_penalty_records_is_active", "penalty_records", ["is_active"])
    op.create_index("idx_penalty_records_created", "penalty_records", ["created_at"])
    op.create_index("idx_penalty_records_appeal_status", "penalty_records", ["appeal_status"])

    # 创建设备封禁表
    op.create_table(
        "device_bans",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("device_fingerprint", sa.String(128), unique=True, nullable=False),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ban_reason", sa.String(500), nullable=False),
        sa.Column("related_penalty_id", sa.CHAR(36), sa.ForeignKey("penalty_records.id", ondelete="SET NULL"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index("idx_device_bans_fingerprint", "device_bans", ["device_fingerprint"])
    op.create_index("idx_device_bans_user_id", "device_bans", ["user_id"])


def downgrade() -> None:
    """回滚处罚表。"""
    op.drop_index("idx_device_bans_user_id", "device_bans")
    op.drop_index("idx_device_bans_fingerprint", "device_bans")
    op.drop_table("device_bans")

    op.drop_index("idx_penalty_records_appeal_status", "penalty_records")
    op.drop_index("idx_penalty_records_created", "penalty_records")
    op.drop_index("idx_penalty_records_is_active", "penalty_records")
    op.drop_index("idx_penalty_records_violation_type", "penalty_records")
    op.drop_index("idx_penalty_records_user_id", "penalty_records")
    op.drop_table("penalty_records")
