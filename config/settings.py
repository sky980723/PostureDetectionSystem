"""
姿态检测系统配置管理模块

使用 Pydantic Settings 提供类型安全的配置管理,支持环境变量覆盖
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class PostureDetectionSettings(BaseSettings):
    """
    姿态检测系统配置类

    所有配置支持通过环境变量覆盖,环境变量格式为 POSTURE_{字段名大写}
    例如: POSTURE_HEAD_FORWARD_ANGLE_THRESHOLD=20.0
    """

    # MediaPipe Pose 配置
    model_complexity: int = Field(
        default=1,
        ge=0,
        le=2,
        description="MediaPipe 模型复杂度 (0=轻量, 1=标准, 2=重量)"
    )

    min_detection_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="最小检测置信度阈值"
    )

    min_tracking_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="最小追踪置信度阈值"
    )

    # 头部前倾检测配置
    head_forward_angle_threshold: float = Field(
        default=15.0,
        ge=0.0,
        description="头部前倾角度阈值(度), 超过此角度判定为前倾"
    )

    # 驼背检测配置
    hunchback_offset_threshold: float = Field(
        default=0.1,
        ge=0.0,
        description="驼背检测偏移量阈值, 肩膀相对髋部的 Y 坐标归一化偏移"
    )

    # 跷二郎腿检测配置
    crossed_legs_x_diff_threshold: float = Field(
        default=0.05,
        ge=0.0,
        description="跷二郎腿检测 X 坐标差异阈值(归一化), 膝盖/脚踝横向偏移"
    )

    # 检测可靠性配置
    min_landmark_visibility: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="关键点最小可见度阈值, 低于此值的关键点将被忽略"
    )

    class Config:
        env_prefix = "POSTURE_"
        case_sensitive = False


# 全局配置实例
settings = PostureDetectionSettings()
