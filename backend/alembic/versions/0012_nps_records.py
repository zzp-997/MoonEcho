"""创建 NPS 评分记录表。

用于收集内测用户的 NPS（Net Promoter Score）评分，
作为验证门控的关键指标之一。

目标：≥ 30 分为达标，< 0 重新评估产品方向
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012_nps_records'
down_revision = '0011_anon_security_fix'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'nps_records',
        sa.Column('id', sa.CHAR(36), nullable=False, comment='主键ID'),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID'),
        sa.Column('score', sa.Integer, nullable=False, comment='NPS 评分（0-10 分）'),
        sa.Column('feedback', sa.Text(), nullable=True, comment='用户反馈（可选）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='NPS 评分记录表',
    )
    op.create_index('idx_nps_records_user_id', 'nps_records', ['user_id'])
    op.create_index('idx_nps_records_created_at', 'nps_records', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_nps_records_created_at', 'nps_records')
    op.drop_index('idx_nps_records_user_id', 'nps_records')
    op.drop_table('nps_records')
