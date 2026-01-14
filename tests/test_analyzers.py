"""
坐姿分析器单元测试

测试 PostureAnalyzer 类的功能,使用构造的关键点数据进行测试
"""

import pytest
import math

from src.analyzers.posture_analyzer import PostureAnalyzer, PostureAnalysisResult
from src.detectors.pose_detector import PoseResult, Landmark, PoseDetector


class TestPostureAnalysisResult:
    """测试 PostureAnalysisResult 数据类"""

    def test_analysis_result_creation(self):
        """测试分析结果创建"""
        result = PostureAnalysisResult(
            head_forward=True,
            head_forward_angle=20.0,
            hunchback=False,
            hunchback_offset=0.15,
            crossed_legs=True,
            crossed_legs_diff=0.08,
            valid=True
        )
        assert result.head_forward is True
        assert result.head_forward_angle == 20.0
        assert result.hunchback is False
        assert result.valid is True

    def test_analysis_result_to_dict(self):
        """测试分析结果转字典"""
        result = PostureAnalysisResult(
            head_forward=True,
            head_forward_angle=20.0,
            hunchback=False,
            hunchback_offset=0.15,
            crossed_legs=False,
            crossed_legs_diff=0.02,
            valid=True
        )
        result_dict = result.to_dict()
        assert result_dict['head_forward'] is True
        assert result_dict['head_forward_angle'] == 20.0
        assert result_dict['valid'] is True


class TestPostureAnalyzer:
    """测试 PostureAnalyzer 类"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return PostureAnalyzer(
            head_forward_threshold=15.0,
            hunchback_threshold=0.1,
            crossed_legs_threshold=0.05
        )

    @pytest.fixture
    def normal_pose(self):
        """创建正常坐姿的关键点数据"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33  # 初始化 33 个点

        # 耳朵 (索引 7)
        landmarks[PoseDetector.LEFT_EAR] = Landmark(x=0.45, y=0.2, z=0.0, visibility=0.9)

        # 肩膀 (索引 11-12)
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.4, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.6, y=0.4, z=0.0, visibility=0.9)

        # 髋部 (索引 23-24)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.4, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.6, y=0.7, z=0.0, visibility=0.9)

        # 膝盖 (索引 25-26) - 修正为更对称（差异<0.05）
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.49, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.51, y=0.85, z=0.0, visibility=0.9)

        # 脚踝 (索引 27-28) - 修正为更对称（差异<0.05）
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.48, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.52, y=0.95, z=0.0, visibility=0.9)

        return PoseResult(landmarks=landmarks, detected=True)

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = PostureAnalyzer(
            head_forward_threshold=20.0,
            hunchback_threshold=0.15,
            crossed_legs_threshold=0.08
        )
        assert analyzer.head_forward_threshold == 20.0
        assert analyzer.hunchback_threshold == 0.15
        assert analyzer.crossed_legs_threshold == 0.08

    def test_analyzer_initialization_with_defaults(self):
        """测试使用默认参数初始化"""
        analyzer = PostureAnalyzer()
        assert analyzer.head_forward_threshold is not None
        assert analyzer.hunchback_threshold is not None
        assert analyzer.crossed_legs_threshold is not None

    def test_analyze_normal_pose(self, analyzer, normal_pose):
        """测试正常坐姿分析"""
        result = analyzer.analyze(normal_pose)

        assert result.valid is True
        assert result.head_forward is False
        assert result.hunchback is False
        assert result.crossed_legs is False

    def test_analyze_no_detection(self, analyzer):
        """测试未检测到人体"""
        pose_result = PoseResult(landmarks=[], detected=False)
        result = analyzer.analyze(pose_result)

        assert result.valid is False
        assert result.head_forward_angle is None
        assert result.hunchback_offset is None
        assert result.crossed_legs_diff is None

    def test_check_head_forward_positive(self, analyzer):
        """测试头部前倾检测 - 前倾情况"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33

        # 头部前倾: 耳朵明显前移
        landmarks[PoseDetector.LEFT_EAR] = Landmark(x=0.5, y=0.2, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.4, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.4, y=0.7, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_forward, angle = analyzer.check_head_forward(pose_result)

        assert is_forward is True
        assert angle is not None
        assert angle > analyzer.head_forward_threshold

    def test_check_head_forward_negative(self, analyzer, normal_pose):
        """测试头部前倾检测 - 正常情况"""
        is_forward, angle = analyzer.check_head_forward(normal_pose)

        assert is_forward is False
        assert angle is not None
        assert angle <= analyzer.head_forward_threshold

    def test_check_head_forward_insufficient_visibility(self, analyzer):
        """测试头部前倾检测 - 关键点不可见"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33

        # 设置低可见度
        landmarks[PoseDetector.LEFT_EAR] = Landmark(x=0.5, y=0.2, z=0.0, visibility=0.3)
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.4, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.4, y=0.7, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_forward, angle = analyzer.check_head_forward(pose_result)

        assert is_forward is False
        assert angle is None

    def test_check_hunchback_positive(self, analyzer):
        """测试驼背检测 - 驼背情况"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33

        # 驼背: 肩膀明显下移
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.4, y=0.6, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.6, y=0.6, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.4, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.6, y=0.7, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_hunchback, offset = analyzer.check_hunchback(pose_result)

        assert is_hunchback is True
        assert offset is not None
        assert offset < analyzer.hunchback_threshold

    def test_check_hunchback_negative(self, analyzer, normal_pose):
        """测试驼背检测 - 正常情况"""
        is_hunchback, offset = analyzer.check_hunchback(normal_pose)

        assert is_hunchback is False
        assert offset is not None
        assert offset >= analyzer.hunchback_threshold

    def test_check_hunchback_insufficient_visibility(self, analyzer):
        """测试驼背检测 - 关键点不可见"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33

        # 设置低可见度
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.4, y=0.4, z=0.0, visibility=0.3)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.6, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.4, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.6, y=0.7, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_hunchback, offset = analyzer.check_hunchback(pose_result)

        assert is_hunchback is False
        assert offset is None

    def test_check_crossed_legs_positive(self, analyzer):
        """测试跷二郎腿检测 - 跷腿情况"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33

        # 跷二郎腿: 左右膝盖/脚踝 X 坐标差异明显
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.3, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.7, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.28, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.72, y=0.95, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_crossed, diff = analyzer.check_crossed_legs(pose_result)

        assert is_crossed is True
        assert diff is not None
        assert diff > analyzer.crossed_legs_threshold

    def test_check_crossed_legs_negative(self, analyzer, normal_pose):
        """测试跷二郎腿检测 - 正常情况"""
        is_crossed, diff = analyzer.check_crossed_legs(normal_pose)

        assert is_crossed is False
        assert diff is not None
        assert diff <= analyzer.crossed_legs_threshold

    def test_check_crossed_legs_insufficient_visibility(self, analyzer):
        """测试跷二郎腿检测 - 关键点不可见"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33

        # 设置低可见度
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.3, y=0.85, z=0.0, visibility=0.3)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.7, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.28, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.72, y=0.95, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_crossed, diff = analyzer.check_crossed_legs(pose_result)

        assert is_crossed is False
        assert diff is None

    def test_vector_calculation(self, analyzer):
        """测试向量计算"""
        point1 = Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)
        point2 = Landmark(x=1.0, y=1.0, z=0.0, visibility=1.0)

        vector = analyzer._vector(point1, point2)
        assert vector == (1.0, 1.0)

    def test_angle_between_vectors(self, analyzer):
        """测试向量夹角计算"""
        # 垂直向量 (90度)
        vector1 = (1.0, 0.0)
        vector2 = (0.0, 1.0)
        angle = analyzer._angle_between_vectors(vector1, vector2)
        assert abs(angle - 90.0) < 0.01

        # 平行向量 (0度)
        vector1 = (1.0, 0.0)
        vector2 = (2.0, 0.0)
        angle = analyzer._angle_between_vectors(vector1, vector2)
        assert abs(angle - 0.0) < 0.01

        # 反向向量 (180度)
        vector1 = (1.0, 0.0)
        vector2 = (-1.0, 0.0)
        angle = analyzer._angle_between_vectors(vector1, vector2)
        assert abs(angle - 180.0) < 0.01

    def test_angle_between_vectors_zero_vector(self, analyzer):
        """测试零向量夹角计算"""
        vector1 = (0.0, 0.0)
        vector2 = (1.0, 1.0)
        angle = analyzer._angle_between_vectors(vector1, vector2)
        assert angle == 0.0

    def test_create_invalid_result(self, analyzer):
        """测试创建无效结果"""
        result = analyzer._create_invalid_result()
        assert result.valid is False
        assert result.head_forward is False
        assert result.head_forward_angle is None
        assert result.hunchback is False
        assert result.hunchback_offset is None
        assert result.crossed_legs is False
        assert result.crossed_legs_diff is None

    def test_analyze_integration(self, analyzer):
        """测试完整分析流程 - 集成测试"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0)] * 33

        # 构造一个头部前倾 + 驼背 + 跷二郎腿的姿态
        # 头部前倾 - 增大X偏移使角度超过15°
        landmarks[PoseDetector.LEFT_EAR] = Landmark(x=0.55, y=0.2, z=0.0, visibility=0.9)
        # 肩膀下移(驼背) - 调整Y坐标使offset < 0.1
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.4, y=0.62, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.6, y=0.62, z=0.0, visibility=0.9)
        # 髋部
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.4, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.6, y=0.7, z=0.0, visibility=0.9)
        # 跷二郎腿
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.3, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.7, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.28, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.72, y=0.95, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        result = analyzer.analyze(pose_result)

        # 验证所有检测都为 True
        assert result.valid is True
        assert result.head_forward is True
        assert result.hunchback is True
        assert result.crossed_legs is True
