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
        hunchback_offset: 驼背偏移量(归一化)
        crossed_legs: 是否跷二郎腿
        crossed_legs_diff: 腿部横向偏移差异(归一化)
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

    基于 MediaPipe Pose 检测的关键点,分析三种不良坐姿:
    1. 头部前倾: 计算耳-肩-髋连线角度
    2. 驼背: 计算肩膀相对髋部的 Y 坐标偏移
    3. 跷二郎腿: 比较膝盖和脚踝的 X 坐标差异
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
            hunchback_threshold: 驼背偏移量阈值
            crossed_legs_threshold: 跷二郎腿 X 坐标差异阈值
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
        1. 获取耳朵、肩膀、髋部的关键点坐标
        2. 计算耳-肩向量与肩-髋向量的夹角
        3. 当夹角超过阈值时判定为前倾

        Args:
            pose_result: 姿态检测结果

        Returns:
            (是否前倾, 前倾角度) 元组
        """
        # 使用左侧关键点(右侧对称)
        ear = pose_result.get_landmark(PoseDetector.LEFT_EAR)
        shoulder = pose_result.get_landmark(PoseDetector.LEFT_SHOULDER)
        hip = pose_result.get_landmark(PoseDetector.LEFT_HIP)

        # 检查关键点可见性
        if not all([
            pose_result.is_landmark_visible(PoseDetector.LEFT_EAR),
            pose_result.is_landmark_visible(PoseDetector.LEFT_SHOULDER),
            pose_result.is_landmark_visible(PoseDetector.LEFT_HIP)
        ]):
            return False, None

        # 计算向量
        ear_to_shoulder = self._vector(ear, shoulder)
        shoulder_to_hip = self._vector(shoulder, hip)

        # 计算夹角
        angle = self._angle_between_vectors(ear_to_shoulder, shoulder_to_hip)

        # 判断是否前倾
        is_forward = angle > self.head_forward_threshold

        return is_forward, angle

    def check_hunchback(self, pose_result: PoseResult) -> tuple[bool, Optional[float]]:
        """
        检测驼背

        算法:
        1. 计算左右肩膀的平均 Y 坐标
        2. 计算左右髋部的平均 Y 坐标
        3. 计算肩膀相对髋部的归一化偏移量
        4. 当偏移量小于阈值(肩膀下移)时判定为驼背

        Args:
            pose_result: 姿态检测结果

        Returns:
            (是否驼背, 偏移量) 元组
        """
        left_shoulder = pose_result.get_landmark(PoseDetector.LEFT_SHOULDER)
        right_shoulder = pose_result.get_landmark(PoseDetector.RIGHT_SHOULDER)
        left_hip = pose_result.get_landmark(PoseDetector.LEFT_HIP)
        right_hip = pose_result.get_landmark(PoseDetector.RIGHT_HIP)

        # 检查关键点可见性
        if not all([
            pose_result.is_landmark_visible(PoseDetector.LEFT_SHOULDER),
            pose_result.is_landmark_visible(PoseDetector.RIGHT_SHOULDER),
            pose_result.is_landmark_visible(PoseDetector.LEFT_HIP),
            pose_result.is_landmark_visible(PoseDetector.RIGHT_HIP)
        ]):
            return False, None

        # 计算平均坐标
        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_y = (left_hip.y + right_hip.y) / 2

        # 计算相对偏移(正常情况下肩膀应高于髋部,Y 坐标更小)
        # 驼背时肩膀下移,偏移量变小
        offset = hip_y - shoulder_y

        # 判断是否驼背
        is_hunchback = offset < self.hunchback_threshold

        return is_hunchback, offset

    def check_crossed_legs(self, pose_result: PoseResult) -> tuple[bool, Optional[float]]:
        """
        检测跷二郎腿

        算法:
        1. 获取左右膝盖和脚踝的 X 坐标
        2. 计算左右膝盖的 X 坐标差异
        3. 计算左右脚踝的 X 坐标差异
        4. 当膝盖或脚踝的横向偏移超过阈值时判定为跷二郎腿

        Args:
            pose_result: 姿态检测结果

        Returns:
            (是否跷二郎腿, 最大偏移差异) 元组
        """
        left_knee = pose_result.get_landmark(PoseDetector.LEFT_KNEE)
        right_knee = pose_result.get_landmark(PoseDetector.RIGHT_KNEE)
        left_ankle = pose_result.get_landmark(PoseDetector.LEFT_ANKLE)
        right_ankle = pose_result.get_landmark(PoseDetector.RIGHT_ANKLE)

        # 检查关键点可见性
        if not all([
            pose_result.is_landmark_visible(PoseDetector.LEFT_KNEE),
            pose_result.is_landmark_visible(PoseDetector.RIGHT_KNEE),
            pose_result.is_landmark_visible(PoseDetector.LEFT_ANKLE),
            pose_result.is_landmark_visible(PoseDetector.RIGHT_ANKLE)
        ]):
            return False, None

        # 计算横向偏移差异
        knee_diff = abs(left_knee.x - right_knee.x)
        ankle_diff = abs(left_ankle.x - right_ankle.x)

        # 取最大偏移
        max_diff = max(knee_diff, ankle_diff)

        # 判断是否跷二郎腿
        is_crossed = max_diff > self.crossed_legs_threshold

        return is_crossed, max_diff

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
