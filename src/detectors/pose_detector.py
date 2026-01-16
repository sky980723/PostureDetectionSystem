"""
人体姿态检测器模块

封装 YOLOv8-Pose 模型,提供简洁的接口用于人体关键点检测
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np
try:
    from ultralytics import YOLO
except ModuleNotFoundError:
    YOLO = None

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

    封装 YOLOv8-Pose 模型,输出 MediaPipe 33 关键点兼容格式

    MediaPipe 关键点索引:
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

    _MEDIAPIPE_KEYPOINT_COUNT = 33
    _COCO_KEYPOINT_COUNT = 17
    _MEDIAPIPE_TO_COCO = {
        NOSE: 0,
        LEFT_EYE: 1,
        RIGHT_EYE: 2,
        LEFT_EAR: 3,
        RIGHT_EAR: 4,
        LEFT_SHOULDER: 5,
        RIGHT_SHOULDER: 6,
        LEFT_ELBOW: 7,
        RIGHT_ELBOW: 8,
        LEFT_WRIST: 9,
        RIGHT_WRIST: 10,
        LEFT_HIP: 11,
        RIGHT_HIP: 12,
        LEFT_KNEE: 13,
        RIGHT_KNEE: 14,
        LEFT_ANKLE: 15,
        RIGHT_ANKLE: 16
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        imgsz: Optional[int] = None,
        conf: Optional[float] = None,
        iou: Optional[float] = None
    ):
        """
        初始化姿态检测器

        Args:
            model_path: YOLOv8-pose 模型路径或名称
            imgsz: 推理输入尺寸
            conf: 置信度阈值
            iou: NMS IoU 阈值
        """
        self.model_path = model_path or settings.yolo_model_path
        self.imgsz = imgsz or settings.yolo_imgsz
        self.conf = conf or settings.yolo_conf
        self.iou = iou or settings.yolo_iou

        if YOLO is None:
            raise ModuleNotFoundError("ultralytics 未安装, 请先安装 ultralytics")

        self.model = YOLO(self.model_path)

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

        results = self.model.predict(
            image,
            imgsz=self.imgsz,
            conf=self.conf,
            iou=self.iou,
            verbose=False
        )

        if not results:
            return PoseResult(landmarks=[], detected=False)

        result = results[0]
        keypoints = getattr(result, "keypoints", None)
        parsed = self._extract_keypoints(keypoints, image.shape)
        if parsed is None:
            return PoseResult(landmarks=[], detected=False)

        keypoints_xy, keypoints_conf = parsed

        best_index = self._select_best_person(keypoints_conf)
        keypoints_xy = keypoints_xy[best_index]
        keypoints_conf = keypoints_conf[best_index]

        landmarks = self._map_to_mediapipe(keypoints_xy, keypoints_conf)
        return PoseResult(landmarks=landmarks, detected=True)

    def _extract_keypoints(
        self,
        keypoints: Any,
        image_shape: Tuple[int, int, int]
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        解析 YOLO 关键点数据

        Args:
            keypoints: YOLO 输出关键点
            image_shape: 输入图像形状

        Returns:
            (keypoints_xy, keypoints_conf) 或 None
        """
        if keypoints is None:
            return None

        xy = None
        normalized = False

        if hasattr(keypoints, "xyn") and keypoints.xyn is not None:
            xy = self._to_numpy(keypoints.xyn)
            normalized = True
        elif hasattr(keypoints, "xy") and keypoints.xy is not None:
            xy = self._to_numpy(keypoints.xy)
        elif hasattr(keypoints, "data") and keypoints.data is not None:
            data = self._to_numpy(keypoints.data)
            if data is not None and data.shape[-1] >= 2:
                xy = data[..., :2]

        if xy is None or xy.size == 0:
            return None

        conf = None
        if hasattr(keypoints, "conf") and keypoints.conf is not None:
            conf = self._to_numpy(keypoints.conf)
        elif hasattr(keypoints, "data") and keypoints.data is not None:
            data = self._to_numpy(keypoints.data)
            if data is not None and data.shape[-1] >= 3:
                conf = data[..., 2]

        if xy.ndim == 2:
            xy = xy[None, ...]

        if conf is None:
            conf = np.zeros((xy.shape[0], xy.shape[1]), dtype=float)
        elif conf.ndim == 1:
            conf = conf[None, ...]

        if not normalized:
            height, width = image_shape[:2]
            if width > 0 and height > 0:
                xy = xy / np.array([width, height])

        return xy.astype(float), conf.astype(float)

    def _to_numpy(self, value: Any) -> Optional[np.ndarray]:
        if value is None:
            return None
        if hasattr(value, "cpu"):
            return value.cpu().numpy()
        return np.asarray(value)

    def _select_best_person(self, keypoints_conf: np.ndarray) -> int:
        if keypoints_conf.size == 0:
            return 0
        scores = keypoints_conf.mean(axis=1)
        return int(np.argmax(scores))

    def _map_to_mediapipe(
        self,
        keypoints_xy: np.ndarray,
        keypoints_conf: np.ndarray
    ) -> List[Landmark]:
        landmarks = [
            Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0)
            for _ in range(self._MEDIAPIPE_KEYPOINT_COUNT)
        ]

        for mediapipe_index, coco_index in self._MEDIAPIPE_TO_COCO.items():
            if coco_index >= keypoints_xy.shape[0]:
                continue
            x, y = keypoints_xy[coco_index]
            visibility = 0.0
            if coco_index < keypoints_conf.shape[0]:
                visibility = float(keypoints_conf[coco_index])
            landmarks[mediapipe_index] = Landmark(
                x=float(x),
                y=float(y),
                z=0.0,
                visibility=visibility
            )

        return landmarks

    def close(self):
        """释放资源"""
        self.model = None

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __del__(self):
        """析构函数"""
        self.close()
