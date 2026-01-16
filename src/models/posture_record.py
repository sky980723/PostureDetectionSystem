"""
PostureRecord 数据模型

定义姿态记录的数据结构
"""

from datetime import datetime
from typing import Literal

from sqlalchemy import Float, Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base

# 姿态类型定义
PostureType = Literal["head_forward", "hunchback", "crossed_legs"]


class PostureRecord(Base):
    """
    姿态记录模型

    存储检测到的不良姿态记录
    """

    __tablename__ = "posture_records"

    # 主键 ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 记录时间
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
        index=True,  # 添加索引以优化时间范围查询
    )

    # 姿态类型: head_forward（头部前倾）, hunchback（驼背）, crossed_legs（跷二郎腿）
    posture_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,  # 添加索引以优化按类型查询
    )

    # 严重程度 (0.0 - 1.0)
    severity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # 持续时间（秒）
    duration_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # 姿态关键点（JSON 字符串，可选）
    pose_landmarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<PostureRecord(id={self.id}, "
            f"timestamp={self.timestamp}, "
            f"posture_type='{self.posture_type}', "
            f"severity={self.severity:.2f}, "
            f"duration={self.duration_seconds:.1f}s)>"
        )

    def to_dict(self) -> dict:
        """
        转换为字典格式

        Returns:
            包含所有字段的字典
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "posture_type": self.posture_type,
            "severity": self.severity,
            "duration_seconds": self.duration_seconds,
            "pose_landmarks": self.pose_landmarks,
        }

    @classmethod
    def validate_posture_type(cls, posture_type: str) -> bool:
        """
        验证姿态类型是否合法

        Args:
            posture_type: 姿态类型字符串

        Returns:
            是否为合法的姿态类型
        """
        valid_types = {"head_forward", "hunchback", "crossed_legs"}
        return posture_type in valid_types

    @classmethod
    def validate_severity(cls, severity: float) -> bool:
        """
        验证严重程度是否在有效范围内

        Args:
            severity: 严重程度值

        Returns:
            是否在 0.0-1.0 范围内
        """
        return 0.0 <= severity <= 1.0
