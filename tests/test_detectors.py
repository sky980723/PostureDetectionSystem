"""
姿态检测器单元测试

测试 PoseDetector 类的功能,使用 Mock 隔离 MediaPipe 依赖
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.detectors.pose_detector import PoseDetector, PoseResult, Landmark


class TestLandmark:
    """测试 Landmark 数据类"""

    def test_landmark_creation(self):
        """测试 Landmark 对象创建"""
        landmark = Landmark(x=0.5, y=0.6, z=0.1, visibility=0.95)
        assert landmark.x == 0.5
        assert landmark.y == 0.6
        assert landmark.z == 0.1
        assert landmark.visibility == 0.95

    def test_landmark_to_dict(self):
        """测试 Landmark 转字典"""
        landmark = Landmark(x=0.1, y=0.2, z=0.3, visibility=0.8)
        result = landmark.to_dict()
        assert result == {
            'x': 0.1,
            'y': 0.2,
            'z': 0.3,
            'visibility': 0.8
        }


class TestPoseResult:
    """测试 PoseResult 数据类"""

    def test_pose_result_creation(self):
        """测试 PoseResult 对象创建"""
        landmarks = [
            Landmark(x=0.1, y=0.2, z=0.0, visibility=0.9),
            Landmark(x=0.3, y=0.4, z=0.0, visibility=0.8)
        ]
        result = PoseResult(landmarks=landmarks, detected=True)
        assert result.detected is True
        assert len(result.landmarks) == 2

    def test_get_landmark_valid_index(self):
        """测试获取有效索引的关键点"""
        landmarks = [
            Landmark(x=0.1, y=0.2, z=0.0, visibility=0.9),
            Landmark(x=0.3, y=0.4, z=0.0, visibility=0.8)
        ]
        result = PoseResult(landmarks=landmarks, detected=True)
        landmark = result.get_landmark(0)
        assert landmark is not None
        assert landmark.x == 0.1

    def test_get_landmark_invalid_index(self):
        """测试获取无效索引的关键点"""
        landmarks = [Landmark(x=0.1, y=0.2, z=0.0, visibility=0.9)]
        result = PoseResult(landmarks=landmarks, detected=True)
        assert result.get_landmark(-1) is None
        assert result.get_landmark(10) is None

    def test_is_landmark_visible(self):
        """测试关键点可见性判断"""
        landmarks = [
            Landmark(x=0.1, y=0.2, z=0.0, visibility=0.9),
            Landmark(x=0.3, y=0.4, z=0.0, visibility=0.3)
        ]
        result = PoseResult(landmarks=landmarks, detected=True)

        # 使用默认阈值 0.5
        assert result.is_landmark_visible(0) is True
        assert result.is_landmark_visible(1) is False

    def test_is_landmark_visible_custom_threshold(self):
        """测试自定义阈值的可见性判断"""
        landmarks = [Landmark(x=0.1, y=0.2, z=0.0, visibility=0.7)]
        result = PoseResult(landmarks=landmarks, detected=True)

        # 自定义阈值
        assert result.is_landmark_visible(0, threshold=0.6) is True
        assert result.is_landmark_visible(0, threshold=0.8) is False

    def test_is_landmark_visible_invalid_index(self):
        """测试无效索引的可见性判断"""
        landmarks = [Landmark(x=0.1, y=0.2, z=0.0, visibility=0.9)]
        result = PoseResult(landmarks=landmarks, detected=True)
        assert result.is_landmark_visible(99) is False


class TestPoseDetector:
    """测试 PoseDetector 类"""

    @pytest.fixture
    def mock_mediapipe(self):
        """创建 MediaPipe Mock"""
        with patch('src.detectors.pose_detector.mp') as mock_mp:
            # Mock Pose 类
            mock_pose_class = MagicMock()
            mock_pose_instance = MagicMock()
            mock_pose_class.return_value = mock_pose_instance

            # 设置 mock 对象
            mock_mp.solutions.pose.Pose = mock_pose_class

            yield mock_mp, mock_pose_instance

    def test_detector_initialization(self, mock_mediapipe):
        """测试检测器初始化"""
        mock_mp, mock_pose_instance = mock_mediapipe

        detector = PoseDetector(
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        assert detector.model_complexity == 1
        assert detector.min_detection_confidence == 0.5
        assert detector.min_tracking_confidence == 0.5

    def test_detector_initialization_with_defaults(self, mock_mediapipe):
        """测试使用默认参数初始化"""
        mock_mp, mock_pose_instance = mock_mediapipe
        detector = PoseDetector()

        # 应使用配置文件中的默认值
        assert detector.model_complexity is not None
        assert detector.min_detection_confidence is not None

    def test_detect_with_valid_image(self, mock_mediapipe):
        """测试有效图像的检测"""
        mock_mp, mock_pose_instance = mock_mediapipe

        # 创建 mock 关键点
        mock_landmark = Mock()
        mock_landmark.x = 0.5
        mock_landmark.y = 0.5
        mock_landmark.z = 0.0
        mock_landmark.visibility = 0.9

        mock_results = Mock()
        mock_results.pose_landmarks = Mock()
        mock_results.pose_landmarks.landmark = [mock_landmark] * 33

        mock_pose_instance.process.return_value = mock_results

        # 执行检测
        detector = PoseDetector()
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        # 验证结果
        assert result.detected is True
        assert len(result.landmarks) == 33
        assert result.landmarks[0].x == 0.5
        assert result.landmarks[0].visibility == 0.9

    def test_detect_no_pose_found(self, mock_mediapipe):
        """测试未检测到人体"""
        mock_mp, mock_pose_instance = mock_mediapipe

        # Mock 未检测到人体
        mock_results = Mock()
        mock_results.pose_landmarks = None

        mock_pose_instance.process.return_value = mock_results

        # 执行检测
        detector = PoseDetector()
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        # 验证结果
        assert result.detected is False
        assert len(result.landmarks) == 0

    def test_detect_invalid_image_type(self, mock_mediapipe):
        """测试无效图像类型"""
        mock_mp, mock_pose_instance = mock_mediapipe

        detector = PoseDetector()

        # 非 numpy 数组
        with pytest.raises(ValueError, match="输入必须是 numpy.ndarray 类型"):
            detector.detect([1, 2, 3])

    def test_detect_invalid_image_shape(self, mock_mediapipe):
        """测试无效图像形状"""
        mock_mp, mock_pose_instance = mock_mediapipe

        detector = PoseDetector()

        # 单通道图像
        image = np.zeros((480, 640), dtype=np.uint8)
        with pytest.raises(ValueError, match="输入图像必须是 3 通道 BGR 图像"):
            detector.detect(image)

        # 4 通道图像
        image = np.zeros((480, 640, 4), dtype=np.uint8)
        with pytest.raises(ValueError, match="输入图像必须是 3 通道 BGR 图像"):
            detector.detect(image)

    def test_bgr_to_rgb_conversion(self, mock_mediapipe):
        """测试 BGR 到 RGB 转换"""
        mock_mp, mock_pose_instance = mock_mediapipe

        detector = PoseDetector()

        # 创建 BGR 图像
        bgr_image = np.zeros((100, 100, 3), dtype=np.uint8)
        bgr_image[:, :, 0] = 255  # Blue channel

        # 转换
        rgb_image = detector._bgr_to_rgb(bgr_image)

        # 验证 Blue 通道转换到 RGB 的第2个通道
        assert rgb_image[0, 0, 2] == 255  # Blue 通道应该还是 255
        assert rgb_image[0, 0, 0] == 0    # Red 通道应该是 0

    def test_context_manager(self, mock_mediapipe):
        """测试上下文管理器"""
        mock_mp, mock_pose_instance = mock_mediapipe

        with PoseDetector() as detector:
            assert detector is not None

        # 验证 close 被调用
        mock_pose_instance.close.assert_called()

    def test_close_method(self, mock_mediapipe):
        """测试 close 方法"""
        mock_mp, mock_pose_instance = mock_mediapipe

        detector = PoseDetector()
        detector.close()

        mock_pose_instance.close.assert_called()

    def test_landmark_constants(self):
        """测试关键点索引常量"""
        assert PoseDetector.NOSE == 0
        assert PoseDetector.LEFT_SHOULDER == 11
        assert PoseDetector.RIGHT_SHOULDER == 12
        assert PoseDetector.LEFT_HIP == 23
        assert PoseDetector.RIGHT_HIP == 24
        assert PoseDetector.LEFT_KNEE == 25
        assert PoseDetector.RIGHT_KNEE == 26
        assert PoseDetector.LEFT_ANKLE == 27
        assert PoseDetector.RIGHT_ANKLE == 28
        assert PoseDetector.LEFT_EAR == 7
        assert PoseDetector.RIGHT_EAR == 8
