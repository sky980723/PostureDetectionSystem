"""
人体姿态检测器模块

封装 MediaPipe Pose 模型,提供简洁的接口用于人体关键点检测
"""

from typing import Optional, List, Dict, Any
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from dataclasses import dataclass
from pathlib import Path

from config.settings import settings


@dataclass
class Landmark:
    """
    人体关键点数据类

    Attributes:
        x: X 坐标 (归一化, 范围 0-1)
        y: Y 坐标 (归一化, 范围 0-1)
        z: Z 坐标 (深度信息, 归一化)
        visibility: 可见度 (范围 0-1, 1 表示完全可见)
    """
    x: float
    y: float
    z: float
    visibility: float

    def to_dict(self) -> Dict[str, float]:
        """转换为字典格式"""
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'visibility': self.visibility
        }


@dataclass
class PoseResult:
    """
    姿态检测结果数据类

    Attributes:
        landmarks: 33 个关键点列表 (MediaPipe Pose 标准)
        detected: 是否成功检测到人体
    """
    landmarks: List[Landmark]
    detected: bool

    def get_landmark(self, index: int) -> Optional[Landmark]:
        """
        获取指定索引的关键点

        Args:
            index: 关键点索引 (0-32)

        Returns:
            关键点对象,如果索引无效则返回 None
        """
        if 0 <= index < len(self.landmarks):
            return self.landmarks[index]
        return None

    def is_landmark_visible(self, index: int, threshold: Optional[float] = None) -> bool:
        """
        检查关键点是否可见

        Args:
            index: 关键点索引
            threshold: 可见度阈值,默认使用配置值

        Returns:
            是否可见
        """
        landmark = self.get_landmark(index)
        if landmark is None:
            return False

        threshold = threshold or settings.min_landmark_visibility
        return landmark.visibility >= threshold


class PoseDetector:
    """
    人体姿态检测器

    封装 MediaPipe Pose 模型,提供简洁易用的人体关键点检测功能

    MediaPipe Pose 关键点索引:
        0: 鼻子 (nose)
        11-12: 肩膀 (left_shoulder, right_shoulder)
        23-24: 髋部 (left_hip, right_hip)
        25-26: 膝盖 (left_knee, right_knee)
        27-28: 脚踝 (left_ankle, right_ankle)
        详见: https://google.github.io/mediapipe/solutions/pose.html
    """

    # MediaPipe Pose 关键点索引常量
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32

    def __init__(
        self,
        model_complexity: Optional[int] = None,
        min_detection_confidence: Optional[float] = None,
        min_tracking_confidence: Optional[float] = None
    ):
        """
        初始化姿态检测器

        Args:
            model_complexity: 模型复杂度 (0=轻量, 1=标准, 2=重量) [注：新版API统一使用lite模型]
            min_detection_confidence: 最小检测置信度
            min_tracking_confidence: 最小追踪置信度
        """
        self.model_complexity = model_complexity or settings.model_complexity
        self.min_detection_confidence = (
            min_detection_confidence or settings.min_detection_confidence
        )
        self.min_tracking_confidence = (
            min_tracking_confidence or settings.min_tracking_confidence
        )

        # 初始化 MediaPipe Pose Landmarker（新版 API）
        model_path = Path(__file__).parent.parent.parent / "models" / "pose_landmarker_lite.task"

        base_options = python.BaseOptions(model_asset_path=str(model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )

        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def detect(self, image: np.ndarray) -> PoseResult:
        """
        检测图像中的人体姿态

        Args:
            image: 输入图像 (RGB 格式)

        Returns:
            PoseResult 对象,包含 33 个关键点数据

        Raises:
            ValueError: 输入图像格式无效
        """
        if not isinstance(image, np.ndarray):
            raise ValueError("输入必须是 numpy.ndarray 类型")

        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(f"输入图像必须是 3 通道图像, 当前形状: {image.shape}")

        # 转换为 MediaPipe Image 对象
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)

        # 执行检测
        detection_result = self.landmarker.detect(mp_image)

        # 解析结果
        if detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0:
            # 取第一个检测到的人体（通常只有一个）
            landmarks = self._parse_landmarks(detection_result.pose_landmarks[0])
            return PoseResult(landmarks=landmarks, detected=True)
        else:
            # 未检测到人体,返回空的关键点列表
            return PoseResult(landmarks=[], detected=False)

    def _bgr_to_rgb(self, image: np.ndarray) -> np.ndarray:
        """
        将 BGR 图像转换为 RGB 格式

        Args:
            image: BGR 格式图像

        Returns:
            RGB 格式图像
        """
        # MediaPipe 需要 RGB 格式且图像不可写
        return np.ascontiguousarray(image[:, :, ::-1])

    def _parse_landmarks(self, mediapipe_landmarks: Any) -> List[Landmark]:
        """
        解析 MediaPipe 关键点数据

        Args:
            mediapipe_landmarks: MediaPipe 原始关键点列表

        Returns:
            标准化的 Landmark 对象列表
        """
        landmarks = []
        for lm in mediapipe_landmarks:
            landmark = Landmark(
                x=lm.x,
                y=lm.y,
                z=lm.z,
                visibility=lm.visibility
            )
            landmarks.append(landmark)
        return landmarks

    def close(self):
        """释放资源"""
        if hasattr(self, 'landmarker'):
            self.landmarker.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __del__(self):
        """析构函数"""
        self.close()
