"""新增 pose_landmarks 字段并清空历史记录"""

from alembic import op
import sqlalchemy as sa

revision = "20250309_add_pose_landmarks_field"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：清空历史记录并新增字段"""
    op.execute("DELETE FROM posture_records")
    op.add_column(
        "posture_records",
        sa.Column("pose_landmarks", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """回滚：移除新增字段"""
    op.drop_column("posture_records", "pose_landmarks")
