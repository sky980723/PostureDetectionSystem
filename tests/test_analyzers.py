"""
坐姿分析器单元测试

测试 PostureAnalyzer 类的功能,使用构造的关键点数据进行测试
"""

import pytest

from src.analyzers.posture_analyzer import PostureAnalyzer, PostureAnalysisResult
from src.detectors.pose_detector import PoseResult, Landmark, PoseDetector
from config.alert_config import AlertConfig
from config.api_settings import api_settings


class TestPostureAnalysisResult:
    """测试 PostureAnalysisResult 数据类"""

    def test_analysis_result_creation(self):
        """测试分析结果创建"""
        result = PostureAnalysisResult(
            head_forward=True,
            head_forward_angle=20.0,
            hunchback=False,
            hunchback_offset=18.0,
            crossed_legs=True,
            crossed_legs_diff=12.0,
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
            hunchback_offset=18.0,
            crossed_legs=False,
            crossed_legs_diff=12.0,
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
            head_forward_threshold=20.0,
            hunchback_threshold=15.0,
            crossed_legs_threshold=10.0
        )

    @pytest.fixture
    def normal_pose(self):
        """创建正常坐姿的关键点数据"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 鼻子
        landmarks[PoseDetector.NOSE] = Landmark(x=0.5, y=0.2, z=0.0, visibility=0.9)

        # 肩膀
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.45, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.55, y=0.4, z=0.0, visibility=0.9)

        # 髋部
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.45, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)

        # 膝盖
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.47, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.53, y=0.85, z=0.0, visibility=0.9)

        # 脚踝
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.47, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.53, y=0.95, z=0.0, visibility=0.9)

        return PoseResult(landmarks=landmarks, detected=True)

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = PostureAnalyzer(
            head_forward_threshold=22.0,
            hunchback_threshold=18.0,
            crossed_legs_threshold=12.0
        )
        assert analyzer.head_forward_threshold == 22.0
        assert analyzer.hunchback_threshold == 18.0
        assert analyzer.crossed_legs_threshold == 12.0

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
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 头部前倾: nose 明显前移
        landmarks[PoseDetector.NOSE] = Landmark(x=0.65, y=0.2, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.45, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.55, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.45, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)

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
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 设置低可见度
        landmarks[PoseDetector.NOSE] = Landmark(x=0.5, y=0.2, z=0.0, visibility=0.3)
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.45, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.55, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.45, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_forward, angle = analyzer.check_head_forward(pose_result)

        assert is_forward is False
        assert angle is None

    def test_check_hunchback_positive(self, analyzer):
        """测试驼背检测 - 驼背情况"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 驼背: 肩髋连线偏离垂直线
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.45, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.55, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.65, y=0.7, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_hunchback, offset = analyzer.check_hunchback(pose_result)

        assert is_hunchback is True
        assert offset is not None
        assert offset > analyzer.hunchback_threshold

    def test_check_hunchback_negative(self, analyzer, normal_pose):
        """测试驼背检测 - 正常情况"""
        is_hunchback, offset = analyzer.check_hunchback(normal_pose)

        assert is_hunchback is False
        assert offset is not None
        assert offset <= analyzer.hunchback_threshold

    def test_check_hunchback_insufficient_visibility(self, analyzer):
        """测试驼背检测 - 关键点不可见"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 设置低可见度
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.45, y=0.4, z=0.0, visibility=0.3)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.55, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.45, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        is_hunchback, offset = analyzer.check_hunchback(pose_result)

        assert is_hunchback is False
        assert offset is None

    def test_check_crossed_legs_positive(self, analyzer):
        """测试跷二郎腿检测 - 跷腿情况"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 跷二郎腿: 左腿跨越身体中线且角度差明显
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.45, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.55, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.45, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.65, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.4, y=0.95, z=0.0, visibility=0.9)

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
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 设置低可见度
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.45, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.55, y=0.85, z=0.0, visibility=0.3)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.45, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.65, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.4, y=0.95, z=0.0, visibility=0.9)

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

    def test_virtual_point_midpoint(self, analyzer):
        """测试虚拟点中点计算"""
        left_shoulder = Landmark(x=0.4, y=0.4, z=0.1, visibility=0.9)
        right_shoulder = Landmark(x=0.6, y=0.4, z=0.3, visibility=0.8)
        left_hip = Landmark(x=0.4, y=0.7, z=0.2, visibility=0.9)
        right_hip = Landmark(x=0.6, y=0.7, z=0.4, visibility=0.7)

        neck = analyzer._midpoint(left_shoulder, right_shoulder)
        torso = analyzer._midpoint(left_hip, right_hip)

        assert neck.x == 0.5
        assert neck.y == 0.4
        assert neck.z == pytest.approx(0.2)
        assert neck.visibility == 0.8
        assert torso.x == 0.5
        assert torso.y == 0.7
        assert torso.z == pytest.approx(0.3)
        assert torso.visibility == 0.7

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
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]

        # 构造一个头部前倾 + 驼背 + 跷二郎腿的姿态
        landmarks[PoseDetector.NOSE] = Landmark(x=0.7, y=0.2, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.45, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.55, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.65, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.65, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.58, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.75, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.57, y=0.95, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        result = analyzer.analyze(pose_result)

        # 验证所有检测都为 True
        assert result.valid is True
        assert result.head_forward is True
        assert result.hunchback is True
        assert result.crossed_legs is True

    def test_analyze_insufficient_visibility_returns_invalid(self, analyzer):
        """测试关键点不可见时返回无效结果"""
        landmarks = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(17)]
        landmarks[PoseDetector.NOSE] = Landmark(x=0.5, y=0.2, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_SHOULDER] = Landmark(x=0.45, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_SHOULDER] = Landmark(x=0.55, y=0.4, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_HIP] = Landmark(x=0.45, y=0.7, z=0.0, visibility=0.2)
        landmarks[PoseDetector.RIGHT_HIP] = Landmark(x=0.55, y=0.7, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_KNEE] = Landmark(x=0.47, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_KNEE] = Landmark(x=0.53, y=0.85, z=0.0, visibility=0.9)
        landmarks[PoseDetector.LEFT_ANKLE] = Landmark(x=0.47, y=0.95, z=0.0, visibility=0.9)
        landmarks[PoseDetector.RIGHT_ANKLE] = Landmark(x=0.53, y=0.95, z=0.0, visibility=0.9)

        pose_result = PoseResult(landmarks=landmarks, detected=True)
        result = analyzer.analyze(pose_result)

        assert result.valid is False
        assert result.head_forward_angle is None
        assert result.hunchback_offset is None
        assert result.crossed_legs_diff is None


class TestConfigCoverage:
    """覆盖配置模块的基础行为"""

    def test_alert_config_methods(self):
        """测试提醒配置方法"""
        assert AlertConfig.get_cooldown_time("warning") == 60.0
        assert AlertConfig.get_cooldown_time("unknown") == AlertConfig.DEFAULT_COOLDOWN_SECONDS
        assert AlertConfig.get_status_color("good") == "green"
        assert AlertConfig.get_status_color("unknown") == "gray"
        assert AlertConfig.get_status_label("bad") == "坐姿不良"
        assert AlertConfig.get_status_label("unknown") == "未知状态"
        assert AlertConfig.get_sound_params("bad")["frequency"] == 880
        assert AlertConfig.get_sound_params("unknown") == AlertConfig.SOUND_PARAMS["warning"]
        assert AlertConfig.get_issue_description("head_forward") == "头部前倾"
        assert AlertConfig.get_issue_description("other") == "other"
        assert AlertConfig.get_issue_suggestions("crossed_legs")
        assert AlertConfig.get_issue_suggestions("other") == []
        assert AlertConfig.POPUP_TITLES["warning"] == "坐姿提醒"

    def test_api_settings_defaults(self):
        """测试 API 配置默认值可用"""
        assert api_settings.app_name
        assert api_settings.app_version
        assert api_settings.port > 0
        assert api_settings.cors_origins
        assert api_settings.default_head_forward_angle >= 0.0
        assert api_settings.default_hunchback_offset >= 0.0
        assert api_settings.default_crossed_legs_diff >= 0.0
