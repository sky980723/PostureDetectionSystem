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

    # YOLOv8-Pose 配置
    yolo_model_path: str = Field(
        default="yolov8n-pose.pt",
        description="YOLOv8-pose 模型路径或名称"
    )

    yolo_imgsz: int = Field(
        default=640,
        ge=1,
        description="YOLO 推理输入尺寸"
    )

    yolo_conf: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="YOLO 置信度阈值"
    )

    yolo_iou: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="YOLO NMS IoU 阈值"
    )

    # 头部前倾检测配置
    head_forward_angle_threshold: float = Field(
        default=20.0,
        ge=0.0,
        description="头部前倾角度阈值(度), 超过此角度判定为前倾"
    )

    # 驼背检测配置
    hunchback_offset_threshold: float = Field(
        default=15.0,
        ge=0.0,
        description="驼背检测偏移角度阈值(度), 肩髋向量与垂直线夹角"
    )

    # 跷二郎腿检测配置
    crossed_legs_x_diff_threshold: float = Field(
        default=10.0,
        ge=0.0,
        description="跷二郎腿检测角度差阈值(度), 膝盖-脚踝向量角度差"
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
