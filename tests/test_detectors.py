"""
姿态检测器单元测试

测试 PoseDetector 类的功能,使用 Mock 隔离 YOLO 依赖
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from config.settings import settings
from src.detectors.pose_detector import PoseDetector, PoseResult, Landmark


class DummyKeypoints:
    """用于测试的 YOLO Keypoints 替身"""

    def __init__(self, xyn: np.ndarray, conf: np.ndarray):
        self.xyn = xyn
        self.conf = conf

    def __len__(self) -> int:
        return len(self.xyn)


class DummyKeypointsNoConf:
    """无置信度字段的 Keypoints"""

    def __init__(self, xyn: np.ndarray):
        self.xyn = xyn


class DummyKeypointsData:
    """仅提供 data 字段的 Keypoints"""

    def __init__(self, data: np.ndarray):
        self.data = data


class DummyKeypointsXY:
    """仅提供 xy 字段的 Keypoints"""

    def __init__(self, xy: np.ndarray):
        self.xy = xy


class DummyTensor:
    """模拟带 cpu/numpy 接口的张量"""

    def __init__(self, value: np.ndarray):
        self.value = value

    def cpu(self):
        return self

    def numpy(self):
        return self.value


def build_dummy_keypoints(person_count: int = 1) -> DummyKeypoints:
    """构建可控的关键点数据"""
    xyn = np.zeros((person_count, 17, 2), dtype=float)
    conf = np.zeros((person_count, 17), dtype=float)

    for person_index in range(person_count):
        for keypoint_index in range(17):
            xyn[person_index, keypoint_index] = [
                (keypoint_index + person_index) / 100.0,
                (keypoint_index + person_index + 1) / 100.0
            ]
            conf[person_index, keypoint_index] = 0.05 + (keypoint_index + person_index) / 100.0

    return DummyKeypoints(xyn=xyn, conf=conf)


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
    def mock_yolo(self):
        """创建 YOLO Mock"""
        with patch('src.detectors.pose_detector.YOLO') as mock_yolo_class:
            mock_model = MagicMock()
            mock_yolo_class.return_value = mock_model
            yield mock_yolo_class, mock_model

    def test_detector_initialization_with_defaults(self, mock_yolo, monkeypatch):
        """测试使用默认参数初始化"""
        mock_yolo_class, _ = mock_yolo

        monkeypatch.setattr(settings, "yolo_model_path", "custom-yolo.pt")
        monkeypatch.setattr(settings, "yolo_imgsz", 512)
        monkeypatch.setattr(settings, "yolo_conf", 0.35)
        monkeypatch.setattr(settings, "yolo_iou", 0.65)

        detector = PoseDetector()

        mock_yolo_class.assert_called_once_with("custom-yolo.pt")
        assert detector.model_path == "custom-yolo.pt"
        assert detector.imgsz == 512
        assert detector.conf == 0.35
        assert detector.iou == 0.65

    def test_detector_initialization_with_overrides(self, mock_yolo):
        """测试显式参数覆盖配置"""
        mock_yolo_class, _ = mock_yolo

        detector = PoseDetector(
            model_path="override.pt",
            imgsz=320,
            conf=0.2,
            iou=0.5
        )

        mock_yolo_class.assert_called_once_with("override.pt")
        assert detector.model_path == "override.pt"
        assert detector.imgsz == 320
        assert detector.conf == 0.2
        assert detector.iou == 0.5

    def test_detector_initialization_requires_ultralytics(self):
        """测试缺少 ultralytics 时抛错"""
        with patch('src.detectors.pose_detector.YOLO', None):
            with pytest.raises(ModuleNotFoundError, match="ultralytics"):
                PoseDetector(model_path="missing.pt")

    def test_detect_with_valid_image_maps_keypoints(self, mock_yolo, monkeypatch):
        """测试有效图像的关键点映射"""
        _, mock_model = mock_yolo

        keypoints = build_dummy_keypoints()
        mock_model.predict.return_value = [Mock(keypoints=keypoints)]

        monkeypatch.setattr(settings, "yolo_model_path", "yolov8n-pose.pt")
        monkeypatch.setattr(settings, "yolo_imgsz", 640)
        monkeypatch.setattr(settings, "yolo_conf", 0.25)
        monkeypatch.setattr(settings, "yolo_iou", 0.7)

        detector = PoseDetector()
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.detected is True
        assert len(result.landmarks) == 33

        nose = result.landmarks[PoseDetector.NOSE]
        assert nose.x == pytest.approx(0.0)
        assert nose.y == pytest.approx(0.01)
        assert nose.z == 0.0
        assert nose.visibility == pytest.approx(0.05)

        left_eye = result.landmarks[PoseDetector.LEFT_EYE]
        assert left_eye.x == pytest.approx(0.01)
        assert left_eye.y == pytest.approx(0.02)

        right_ankle = result.landmarks[PoseDetector.RIGHT_ANKLE]
        assert right_ankle.x == pytest.approx(0.16)
        assert right_ankle.y == pytest.approx(0.17)

        left_eye_inner = result.landmarks[PoseDetector.LEFT_EYE_INNER]
        assert left_eye_inner.x == 0.0
        assert left_eye_inner.y == 0.0
        assert left_eye_inner.z == 0.0
        assert left_eye_inner.visibility == 0.0

        mock_model.predict.assert_called_once_with(
            image,
            imgsz=640,
            conf=0.25,
            iou=0.7,
            verbose=False
        )

    def test_detect_selects_best_person(self, mock_yolo):
        """测试多人体时选取最高置信度"""
        _, mock_model = mock_yolo

        xyn = np.zeros((2, 17, 2), dtype=float)
        conf = np.zeros((2, 17), dtype=float)

        xyn[0, :, 0] = 0.1
        xyn[0, :, 1] = 0.1
        conf[0, :] = 0.1

        xyn[1, :, 0] = 0.9
        xyn[1, :, 1] = 0.9
        conf[1, :] = 0.9

        mock_model.predict.return_value = [Mock(keypoints=DummyKeypoints(xyn=xyn, conf=conf))]

        detector = PoseDetector(model_path="mock.pt")
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.detected is True
        assert result.landmarks[PoseDetector.NOSE].x == pytest.approx(0.9)

    def test_detect_empty_results(self, mock_yolo):
        """测试空帧返回空结果"""
        _, mock_model = mock_yolo
        mock_model.predict.return_value = []

        detector = PoseDetector(model_path="mock.pt")
        image = np.zeros((0, 0, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.detected is False
        assert result.landmarks == []

    def test_detect_no_pose_found(self, mock_yolo):
        """测试未检测到人体"""
        _, mock_model = mock_yolo

        mock_model.predict.return_value = [Mock(keypoints=None)]

        detector = PoseDetector(model_path="mock.pt")
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.detected is False
        assert len(result.landmarks) == 0

    def test_extract_keypoints_from_data_and_normalize(self, mock_yolo):
        """测试从 data 解析并归一化"""
        detector = PoseDetector(model_path="mock.pt")

        data = np.zeros((1, 17, 3), dtype=float)
        data[0, 0] = [100.0, 50.0, 0.8]
        keypoints = DummyKeypointsData(data=data)

        keypoints_xy, keypoints_conf = detector._extract_keypoints(keypoints, (100, 200, 3))

        assert keypoints_xy.shape == (1, 17, 2)
        assert keypoints_xy[0, 0, 0] == pytest.approx(0.5)
        assert keypoints_xy[0, 0, 1] == pytest.approx(0.5)
        assert keypoints_conf[0, 0] == pytest.approx(0.8)

    def test_extract_keypoints_empty_returns_none(self, mock_yolo):
        """测试空关键点返回 None"""
        detector = PoseDetector(model_path="mock.pt")

        empty_keypoints = DummyKeypoints(xyn=np.zeros((0, 17, 2)), conf=np.zeros((0, 17)))
        assert detector._extract_keypoints(empty_keypoints, (100, 100, 3)) is None

    def test_extract_keypoints_defaults_conf(self, mock_yolo):
        """测试缺失置信度时填充为 0"""
        detector = PoseDetector(model_path="mock.pt")

        keypoints = DummyKeypointsNoConf(xyn=np.zeros((17, 2), dtype=float))
        keypoints_xy, keypoints_conf = detector._extract_keypoints(keypoints, (100, 100, 3))

        assert keypoints_xy.shape == (1, 17, 2)
        assert keypoints_conf.shape == (1, 17)
        assert float(keypoints_conf.sum()) == 0.0

    def test_extract_keypoints_reshape_conf(self, mock_yolo):
        """测试一维置信度扩展"""
        detector = PoseDetector(model_path="mock.pt")

        keypoints = DummyKeypoints(xyn=np.zeros((17, 2), dtype=float), conf=np.zeros(17))
        keypoints_xy, keypoints_conf = detector._extract_keypoints(keypoints, (100, 100, 3))

        assert keypoints_xy.shape == (1, 17, 2)
        assert keypoints_conf.shape == (1, 17)

    def test_extract_keypoints_from_xy_normalize(self, mock_yolo):
        """测试从 xy 解析并归一化"""
        detector = PoseDetector(model_path="mock.pt")

        keypoints = DummyKeypointsXY(xy=np.array([[10.0, 20.0]], dtype=float))
        keypoints_xy, keypoints_conf = detector._extract_keypoints(keypoints, (100, 200, 3))

        assert keypoints_xy.shape == (1, 1, 2)
        assert keypoints_xy[0, 0, 0] == pytest.approx(0.05)
        assert keypoints_xy[0, 0, 1] == pytest.approx(0.2)
        assert float(keypoints_conf.sum()) == 0.0

    def test_to_numpy_handles_none_and_cpu(self, mock_yolo):
        """测试 _to_numpy 的边界处理"""
        detector = PoseDetector(model_path="mock.pt")

        assert detector._to_numpy(None) is None

        tensor = DummyTensor(np.array([1.0, 2.0]))
        result = detector._to_numpy(tensor)
        assert np.allclose(result, np.array([1.0, 2.0]))

    def test_select_best_person_empty(self, mock_yolo):
        """测试空置信度数组"""
        detector = PoseDetector(model_path="mock.pt")

        assert detector._select_best_person(np.array([])) == 0

    def test_map_to_mediapipe_handles_missing_points(self, mock_yolo):
        """测试映射时缺失关键点的处理"""
        detector = PoseDetector(model_path="mock.pt")

        keypoints_xy = np.array([[0.4, 0.6]], dtype=float)
        keypoints_conf = np.array([0.8], dtype=float)
        landmarks = detector._map_to_mediapipe(keypoints_xy, keypoints_conf)

        assert landmarks[PoseDetector.NOSE].x == pytest.approx(0.4)
        assert landmarks[PoseDetector.LEFT_EYE].x == 0.0

    def test_map_to_mediapipe_yolo_mapping(self, mock_yolo):
        """测试 YOLO 17→33 关键点映射"""
        detector = PoseDetector(model_path="mock.pt")

        keypoints_xy = np.zeros((17, 2), dtype=float)
        keypoints_conf = np.zeros(17, dtype=float)
        keypoints_xy[0] = [0.11, 0.12]
        keypoints_xy[1] = [0.21, 0.22]
        keypoints_xy[2] = [0.31, 0.32]
        keypoints_conf[0] = 0.95
        keypoints_conf[1] = 0.85
        keypoints_conf[2] = 0.75

        landmarks = detector._map_to_mediapipe(keypoints_xy, keypoints_conf)

        assert landmarks[PoseDetector.NOSE].x == pytest.approx(0.11)
        assert landmarks[PoseDetector.LEFT_EYE].x == pytest.approx(0.21)
        assert landmarks[PoseDetector.RIGHT_EYE].x == pytest.approx(0.31)
        assert landmarks[PoseDetector.RIGHT_EYE].visibility == pytest.approx(0.75)
        assert landmarks[PoseDetector.LEFT_EYE_INNER].visibility == 0.0

    def test_map_to_mediapipe_partial_low_confidence(self, mock_yolo):
        """测试部分关键点低置信度"""
        detector = PoseDetector(model_path="mock.pt")

        keypoints_xy = np.zeros((17, 2), dtype=float)
        keypoints_conf = np.zeros(17, dtype=float)
        keypoints_xy[0] = [0.4, 0.4]
        keypoints_xy[5] = [0.6, 0.6]
        keypoints_conf[0] = 0.02
        keypoints_conf[5] = 0.9

        landmarks = detector._map_to_mediapipe(keypoints_xy, keypoints_conf)

        assert landmarks[PoseDetector.NOSE].visibility == pytest.approx(0.02)
        assert landmarks[PoseDetector.LEFT_SHOULDER].visibility == pytest.approx(0.9)
        assert landmarks[PoseDetector.RIGHT_EYE].visibility == 0.0

    def test_detect_invalid_image_type(self, mock_yolo):
        """测试无效图像类型"""
        detector = PoseDetector(model_path="mock.pt")

        with pytest.raises(ValueError, match="输入必须是 numpy.ndarray 类型"):
            detector.detect([1, 2, 3])

    def test_detect_invalid_image_shape(self, mock_yolo):
        """测试无效图像形状"""
        detector = PoseDetector(model_path="mock.pt")

        image = np.zeros((480, 640), dtype=np.uint8)
        with pytest.raises(ValueError, match="输入图像必须是 3 通道图像"):
            detector.detect(image)

        image = np.zeros((480, 640, 4), dtype=np.uint8)
        with pytest.raises(ValueError, match="输入图像必须是 3 通道图像"):
            detector.detect(image)

    def test_context_manager(self, mock_yolo):
        """测试上下文管理器"""
        with PoseDetector(model_path="mock.pt") as detector:
            assert detector is not None

        assert detector.model is None

    def test_close_method(self, mock_yolo):
        """测试 close 方法"""
        detector = PoseDetector(model_path="mock.pt")
        detector.close()
        assert detector.model is None

    def test_del_method(self, mock_yolo):
        """测试析构函数"""
        detector = PoseDetector(model_path="mock.pt")
        detector.__del__()
        assert detector.model is None

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
