"""
坐姿分析器模块

实现基于人体关键点的坐姿分析算法,包括头部前倾、驼背和跷二郎腿检测
"""

from typing import Optional, Dict, Any
import math
from dataclasses import dataclass

from src.detectors.pose_detector import PoseResult, Landmark, PoseDetector
from config.settings import settings


@dataclass
class PostureAnalysisResult:
    """
    坐姿分析结果数据类

    Attributes:
        head_forward: 是否头部前倾
        head_forward_angle: 头部前倾角度(度)
        hunchback: 是否驼背
        hunchback_offset: 驼背偏移角度(度)
        crossed_legs: 是否跷二郎腿
        crossed_legs_diff: 腿部角度差异(度)
        valid: 分析结果是否有效(所需关键点是否可见)
    """
    head_forward: bool
    head_forward_angle: Optional[float]
    hunchback: bool
    hunchback_offset: Optional[float]
    crossed_legs: bool
    crossed_legs_diff: Optional[float]
    valid: bool

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'head_forward': self.head_forward,
            'head_forward_angle': self.head_forward_angle,
            'hunchback': self.hunchback,
            'hunchback_offset': self.hunchback_offset,
            'crossed_legs': self.crossed_legs,
            'crossed_legs_diff': self.crossed_legs_diff,
            'valid': self.valid
        }


class PostureAnalyzer:
    """
    坐姿分析器

    基于 YOLO COCO 17 关键点,分析三种不良坐姿:
    1. 头部前倾: nose-neck-torso 夹角
    2. 驼背: shoulder_mid->hip_mid 向量与垂直线的偏移角
    3. 跷二郎腿: 膝盖-脚踝向量的角度差 + 跨中线判断
    """

    def __init__(
        self,
        head_forward_threshold: Optional[float] = None,
        hunchback_threshold: Optional[float] = None,
        crossed_legs_threshold: Optional[float] = None
    ):
        """
        初始化坐姿分析器

        Args:
            head_forward_threshold: 头部前倾角度阈值(度)
            hunchback_threshold: 驼背偏移角度阈值(度)
            crossed_legs_threshold: 跷二郎腿角度差阈值(度)
        """
        self.head_forward_threshold = (
            head_forward_threshold or settings.head_forward_angle_threshold
        )
        self.hunchback_threshold = (
            hunchback_threshold or settings.hunchback_offset_threshold
        )
        self.crossed_legs_threshold = (
            crossed_legs_threshold or settings.crossed_legs_x_diff_threshold
        )

    def analyze(self, pose_result: PoseResult) -> PostureAnalysisResult:
        """
        分析坐姿

        Args:
            pose_result: 姿态检测结果

        Returns:
            PostureAnalysisResult 对象,包含所有分析结果
        """
        if not pose_result.detected or not pose_result.landmarks:
            return self._create_invalid_result()

        # 执行三种检测
        head_forward, head_angle = self.check_head_forward(pose_result)
        hunchback, hunch_offset = self.check_hunchback(pose_result)
        crossed_legs, legs_diff = self.check_crossed_legs(pose_result)

        # 判断结果是否有效
        valid = (
            head_angle is not None or
            hunch_offset is not None or
            legs_diff is not None
        )

        return PostureAnalysisResult(
            head_forward=head_forward,
            head_forward_angle=head_angle,
            hunchback=hunchback,
            hunchback_offset=hunch_offset,
            crossed_legs=crossed_legs,
            crossed_legs_diff=legs_diff,
            valid=valid
        )

    def check_head_forward(self, pose_result: PoseResult) -> tuple[bool, Optional[float]]:
        """
        检测头部前倾

        算法:
        1. 计算虚拟 neck 点(肩膀中点)与 torso 点(髋部中点)
        2. 计算 nose->neck 与 neck->torso 的夹角
        3. 当夹角超过阈值时判定为前倾

        Args:
            pose_result: 姿态检测结果

        Returns:
            (是否前倾, 前倾角度) 元组
        """
        indices = [
            PoseDetector.NOSE,
            PoseDetector.LEFT_SHOULDER,
            PoseDetector.RIGHT_SHOULDER,
            PoseDetector.LEFT_HIP,
            PoseDetector.RIGHT_HIP
        ]
        landmarks = self._get_visible_landmarks(pose_result, indices)
        if landmarks is None:
            return False, None

        nose, left_shoulder, right_shoulder, left_hip, right_hip = landmarks
        neck = self._midpoint(left_shoulder, right_shoulder)
        torso = self._midpoint(left_hip, right_hip)

        nose_to_neck = self._vector(nose, neck)
        neck_to_torso = self._vector(neck, torso)
        angle = self._angle_between_vectors(nose_to_neck, neck_to_torso)

        # 判断是否前倾
        is_forward = angle > self.head_forward_threshold

        return is_forward, angle

    def check_hunchback(self, pose_result: PoseResult) -> tuple[bool, Optional[float]]:
        """
        检测驼背

        算法:
        1. 计算肩膀中点与髋部中点
        2. 计算 shoulder_mid->hip_mid 与垂直向量夹角
        3. 当偏移角超过阈值时判定为驼背

        Args:
            pose_result: 姿态检测结果

        Returns:
            (是否驼背, 偏移角度) 元组
        """
        indices = [
            PoseDetector.LEFT_SHOULDER,
            PoseDetector.RIGHT_SHOULDER,
            PoseDetector.LEFT_HIP,
            PoseDetector.RIGHT_HIP
        ]
        landmarks = self._get_visible_landmarks(pose_result, indices)
        if landmarks is None:
            return False, None

        left_shoulder, right_shoulder, left_hip, right_hip = landmarks
        shoulder_mid = self._midpoint(left_shoulder, right_shoulder)
        hip_mid = self._midpoint(left_hip, right_hip)

        spine_vector = self._vector(shoulder_mid, hip_mid)
        vertical_vector = (0.0, 1.0)
        angle = self._angle_between_vectors(spine_vector, vertical_vector)

        is_hunchback = angle > self.hunchback_threshold

        return is_hunchback, angle

    def check_crossed_legs(self, pose_result: PoseResult) -> tuple[bool, Optional[float]]:
        """
        检测跷二郎腿

        算法:
        1. 计算膝盖->脚踝向量与垂直线夹角
        2. 计算左右腿角度差异
        3. 检测是否跨越身体中线
        4. 当角度差超过阈值且跨中线时判定为跷二郎腿

        Args:
            pose_result: 姿态检测结果

        Returns:
            (是否跷二郎腿, 角度差异) 元组
        """
        indices = [
            PoseDetector.LEFT_HIP,
            PoseDetector.RIGHT_HIP,
            PoseDetector.LEFT_KNEE,
            PoseDetector.RIGHT_KNEE,
            PoseDetector.LEFT_ANKLE,
            PoseDetector.RIGHT_ANKLE
        ]
        landmarks = self._get_visible_landmarks(pose_result, indices)
        if landmarks is None:
            return False, None

        left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle = landmarks
        hip_mid = self._midpoint(left_hip, right_hip)
        vertical_vector = (0.0, 1.0)

        left_vector = self._vector(left_knee, left_ankle)
        right_vector = self._vector(right_knee, right_ankle)
        left_angle = self._angle_between_vectors(left_vector, vertical_vector)
        right_angle = self._angle_between_vectors(right_vector, vertical_vector)
        angle_diff = abs(left_angle - right_angle)

        left_crosses = left_knee.x > hip_mid.x or left_ankle.x > hip_mid.x
        right_crosses = right_knee.x < hip_mid.x or right_ankle.x < hip_mid.x
        crosses_midline = left_crosses or right_crosses

        is_crossed = crosses_midline and angle_diff > self.crossed_legs_threshold

        return is_crossed, angle_diff

    def _get_visible_landmarks(
        self,
        pose_result: PoseResult,
        indices: list[int]
    ) -> Optional[list[Landmark]]:
        """
        获取可见的关键点列表

        Args:
            pose_result: 姿态检测结果
            indices: 关键点索引列表

        Returns:
            关键点列表,若任意关键点不可见则返回 None
        """
        landmarks: list[Landmark] = []
        for index in indices:
            landmark = pose_result.get_landmark(index)
            if landmark is None or not pose_result.is_landmark_visible(index):
                return None
            landmarks.append(landmark)
        return landmarks

    def _midpoint(self, point1: Landmark, point2: Landmark) -> Landmark:
        """
        计算两个关键点的中点

        Args:
            point1: 第一个关键点
            point2: 第二个关键点

        Returns:
            中点 Landmark
        """
        return Landmark(
            x=(point1.x + point2.x) / 2,
            y=(point1.y + point2.y) / 2,
            z=(point1.z + point2.z) / 2,
            visibility=min(point1.visibility, point2.visibility)
        )

    def _vector(self, point1: Landmark, point2: Landmark) -> tuple[float, float]:
        """
        计算从 point1 到 point2 的向量

        Args:
            point1: 起点
            point2: 终点

        Returns:
            (dx, dy) 向量
        """
        return (point2.x - point1.x, point2.y - point1.y)

    def _angle_between_vectors(
        self,
        vector1: tuple[float, float],
        vector2: tuple[float, float]
    ) -> float:
        """
        计算两个向量之间的夹角(度数)

        Args:
            vector1: 第一个向量 (x, y)
            vector2: 第二个向量 (x, y)

        Returns:
            夹角(度), 范围 0-180
        """
        # 计算向量模长
        mag1 = math.sqrt(vector1[0]**2 + vector1[1]**2)
        mag2 = math.sqrt(vector2[0]**2 + vector2[1]**2)

        # 避免除零
        if mag1 == 0 or mag2 == 0:
            return 0.0

        # 计算点积
        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]

        # 计算夹角(弧度)
        cos_angle = dot_product / (mag1 * mag2)

        # 限制范围到 [-1, 1] 避免浮点误差
        cos_angle = max(-1.0, min(1.0, cos_angle))

        # 转换为角度
        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

    def _create_invalid_result(self) -> PostureAnalysisResult:
        """创建无效的分析结果"""
        return PostureAnalysisResult(
            head_forward=False,
            head_forward_angle=None,
            hunchback=False,
            hunchback_offset=None,
            crossed_legs=False,
            crossed_legs_diff=None,
            valid=False
        )
