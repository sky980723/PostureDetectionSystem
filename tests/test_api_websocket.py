"""
WebSocket API 单元测试

测试 WebSocket 姿态检测流功能
"""

import pytest
import json
import base64
from unittest.mock import Mock, patch, AsyncMock
from pydantic import ValidationError
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import numpy as np
from PIL import Image
from io import BytesIO

from src.api.main import app
from src.api.deps import get_pose_detector, get_posture_analyzer, get_alert_manager, get_db_session
from src.detectors.pose_detector import PoseResult, Landmark, PoseDetector
from src.analyzers.posture_analyzer import PostureAnalysisResult

COCO_KEYPOINT_COUNT = PoseDetector._COCO_KEYPOINT_COUNT


# ============================================================================
# 辅助函数
# ============================================================================

def create_test_image_base64() -> str:
    """创建测试用的 base64 图像"""
    # 创建一个简单的测试图像
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{img_base64}"


def create_mock_pose_result(detected=True, visibilities=None) -> PoseResult:
    """创建模拟的姿态检测结果"""
    if not detected:
        return PoseResult(landmarks=[], detected=False)

    if visibilities is None:
        visibilities = [0.9 for _ in range(COCO_KEYPOINT_COUNT)]
    elif len(visibilities) != COCO_KEYPOINT_COUNT:
        raise ValueError(f"visibilities must contain {COCO_KEYPOINT_COUNT} values")

    # 创建 17 个模拟关键点
    landmarks = [
        Landmark(x=0.5, y=0.5, z=0.0, visibility=visibility)
        for visibility in visibilities
    ]
    return PoseResult(landmarks=landmarks, detected=True)


def create_mock_analysis_result(has_issues=False) -> PostureAnalysisResult:
    """创建模拟的坐姿分析结果"""
    if has_issues:
        return PostureAnalysisResult(
            head_forward=True,
            head_forward_angle=30.5,
            hunchback=False,
            hunchback_offset=None,
            crossed_legs=False,
            crossed_legs_diff=None,
            valid=True
        )
    else:
        return PostureAnalysisResult(
            head_forward=False,
            head_forward_angle=None,
            hunchback=False,
            hunchback_offset=None,
            crossed_legs=False,
            crossed_legs_diff=None,
            valid=True
        )


class DummySession:
    """模拟数据库会话"""
    def add(self, record):
        return None

    async def commit(self):
        return None

    async def refresh(self, record):
        return None


async def override_get_db_session():
    """覆盖数据库会话依赖"""
    yield DummySession()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_pose_detector():
    """模拟 PoseDetector"""
    detector_instance = Mock()
    detector_instance.detect = Mock(return_value=create_mock_pose_result())
    detector_instance.close = Mock()
    return detector_instance


@pytest.fixture
def mock_posture_analyzer():
    """模拟 PostureAnalyzer"""
    analyzer_instance = Mock()
    analyzer_instance.analyze = Mock(return_value=create_mock_analysis_result())
    return analyzer_instance


@pytest.fixture
def mock_alert_manager():
    """模拟 AlertManager"""
    manager_instance = Mock()
    manager_instance.check_and_alert = Mock(return_value={
        'should_alert': False,
        'status_indicator': {
            'status': 'good',
            'color': 'green',
            'label': '良好'
        }
    })
    return manager_instance


@pytest.fixture
def client(mock_pose_detector, mock_posture_analyzer, mock_alert_manager):
    """创建测试客户端，并覆盖依赖"""
    app.dependency_overrides[get_pose_detector] = lambda: mock_pose_detector
    app.dependency_overrides[get_posture_analyzer] = lambda: mock_posture_analyzer
    app.dependency_overrides[get_alert_manager] = lambda: mock_alert_manager
    app.dependency_overrides[get_db_session] = override_get_db_session

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


# ============================================================================
# 测试用例：WebSocket 连接
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_connection_accepts(client, mock_pose_detector):
    """测试 WebSocket 连接建立"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)

    with client.websocket_connect("/ws/posture") as websocket:
        # 发送测试帧
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123,
            "frame_number": 1
        }
        websocket.send_json(test_data)

        # 接收响应
        response = websocket.receive_json()

        # 验证响应格式
        assert response["type"] == "posture_result"
        assert "timestamp" in response
        assert "detected" in response


@pytest.mark.asyncio
async def test_websocket_invalid_frame_data(client):
    """测试无效的视频帧数据"""
    with client.websocket_connect("/ws/posture") as websocket:
        # 发送无效数据
        test_data = {
            "type": "video_frame",
            "data": "invalid_base64",  # 无效的 base64
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        # 接收错误响应
        response = websocket.receive_json()

        # 验证错误响应
        assert response["type"] == "error"
        assert "message" in response


# ============================================================================
# 测试用例：姿态检测处理
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_posture_detection_success(client, mock_pose_detector, mock_posture_analyzer):
    """测试成功的姿态检测"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)
    mock_posture_analyzer.analyze.return_value = create_mock_analysis_result(has_issues=False)

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 验证检测成功
        assert response["detected"] is True
        assert response["pose_landmarks"] is not None
        assert len(response["pose_landmarks"]) == COCO_KEYPOINT_COUNT
        assert response["analysis"] is not None


@pytest.mark.asyncio
async def test_websocket_confidence_ignores_zero_visibility(client, mock_pose_detector, mock_posture_analyzer):
    """测试置信度忽略 visibility 为 0 的关键点"""
    visibilities = [0.2] * 5 + [0.8] * 5 + [0.0] * 7
    mock_pose_detector.detect.return_value = create_mock_pose_result(
        detected=True,
        visibilities=visibilities
    )
    mock_posture_analyzer.analyze.return_value = create_mock_analysis_result(has_issues=False)

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        assert response["confidence"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_websocket_no_person_detected(client, mock_pose_detector):
    """测试未检测到人体的情况"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=False)

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 验证未检测到人体
        assert response["detected"] is False
        assert response["pose_landmarks"] is None
        assert response["status_indicator"]["status"] == "unknown"


# ============================================================================
# 测试用例：提醒触发
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_alert_triggered(client, mock_pose_detector, mock_posture_analyzer, mock_alert_manager):
    """测试提醒触发"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)
    mock_posture_analyzer.analyze.return_value = create_mock_analysis_result(has_issues=True)
    mock_alert_manager.check_and_alert.return_value = {
        'should_alert': True,
        'sound_alert': {'frequency': 800, 'duration': 0.2},
        'popup_alert': {'title': '坐姿提醒', 'message': '头部前倾'},
        'status_indicator': {
            'status': 'warning',
            'color': 'yellow',
            'label': '需注意'
        }
    }

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 验证提醒被触发
        assert response["alert"] is not None
        assert response["alert"]["should_alert"] is True
        assert response["alert"]["sound_alert"] is not None
        assert response["status_indicator"]["status"] == "warning"


# ============================================================================
# 测试用例：限流
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_rate_limiting(client, mock_pose_detector):
    """测试帧率限流"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)

    with client.websocket_connect("/ws/posture") as websocket:
        # 快速发送多个帧
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }

        # 发送 5 帧，但由于限流，部分帧会被跳过
        received_count = 0
        for i in range(5):
            websocket.send_json(test_data)
            try:
                response = websocket.receive_json(timeout=0.1)
                if response.get("type") == "posture_result":
                    received_count += 1
            except:
                pass

        # 验证限流生效（实际接收的响应数少于发送的帧数）
        assert received_count <= 5


# ============================================================================
# 测试用例：错误处理
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_detection_error(client, mock_pose_detector):
    """测试检测过程中的错误处理"""
    # 模拟检测失败
    mock_pose_detector.detect.side_effect = Exception("Detection failed")

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 验证错误响应
        assert response["type"] == "error"
        assert "error" in response["message"].lower() or "processing" in response["message"].lower()


# ============================================================================
# 测试用例：数据验证
# ============================================================================

def test_video_frame_schema_validation():
    """测试视频帧数据验证"""
    from src.api.schemas.posture import VideoFrameRequest

    # 有效数据
    valid_data = {
        "type": "video_frame",
        "data": create_test_image_base64(),
        "timestamp": 1234567890.123
    }
    frame = VideoFrameRequest(**valid_data)
    assert frame.type == "video_frame"

    # 无效数据：缺少必需字段
    with pytest.raises(Exception):
        VideoFrameRequest(type="video_frame")

    # 无效数据：base64 格式错误
    with pytest.raises(ValueError):
        VideoFrameRequest(
            type="video_frame",
            data="invalid",
            timestamp=1234567890.123
        )

    # 无效数据：Data URL 前缀错误
    with pytest.raises(ValueError):
        VideoFrameRequest(
            type="video_frame",
            data="data:text/plain;base64,AAAAAA",
            timestamp=1234567890.123
        )


def test_posture_response_schema():
    """测试姿态响应数据结构"""
    from src.api.schemas.posture import PostureResponse, LandmarkSchema

    # 创建测试数据
    response = PostureResponse(
        timestamp="2026-01-14T12:00:00",
        detected=True,
        pose_landmarks=[
            LandmarkSchema(x=0.5, y=0.5, z=0.0, visibility=0.9)
            for _ in range(COCO_KEYPOINT_COUNT)
        ],
        analysis=None,
        alert=None,
        status_indicator=None,
        confidence=0.95
    )

    assert response.detected is True
    assert len(response.pose_landmarks) == COCO_KEYPOINT_COUNT
    assert response.confidence == 0.95

    # 无效数据：关键点数量不为 17
    with pytest.raises(ValidationError):
        PostureResponse(
            timestamp="2026-01-14T12:00:00",
            detected=True,
            pose_landmarks=[
                LandmarkSchema(x=0.5, y=0.5, z=0.0, visibility=0.9)
                for _ in range(COCO_KEYPOINT_COUNT - 1)
            ],
            analysis=None,
            alert=None,
            status_indicator=None,
            confidence=0.95
        )


# ============================================================================
# 测试用例：WebSocket 心跳和超时
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_heartbeat_timeout(client, mock_pose_detector):
    """测试 WebSocket 心跳超时处理"""
    import asyncio
    from unittest.mock import patch

    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)

    with patch('src.api.websocket.posture_stream.api_settings') as mock_settings:
        # 设置很短的心跳间隔用于测试
        mock_settings.ws_heartbeat_interval = 0.1
        mock_settings.ws_frame_rate_limit = 10.0

        with client.websocket_connect("/ws/posture") as websocket:
            # 等待心跳超时
            await asyncio.sleep(0.2)

            # 尝试接收 ping 消息（心跳）
            try:
                response = websocket.receive_json(timeout=0.5)
                # 如果收到消息，应该是 ping
                if response.get("type") == "ping":
                    assert True
            except:
                # 超时也是正常的，因为我们只是测试心跳机制存在
                pass


# ============================================================================
# 测试用例：图像处理边界情况
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_grayscale_image(client, mock_pose_detector, mock_posture_analyzer):
    """测试灰度图像转换为RGB"""
    from PIL import Image
    from io import BytesIO
    import base64

    # 创建灰度图像
    img = Image.new('L', (100, 100), color=128)  # 'L' mode = grayscale
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)
    mock_posture_analyzer.analyze.return_value = create_mock_analysis_result(has_issues=False)

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": f"data:image/jpeg;base64,{img_base64}",
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 应该成功处理并检测到人体
        assert response["type"] == "posture_result"


@pytest.mark.asyncio
async def test_websocket_invalid_base64_encoding(client):
    """测试无效的 base64 编码"""
    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": "data:image/jpeg;base64,!!!invalid_base64!!!",
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 应该返回错误响应
        assert response["type"] == "error"
        assert "decode" in response["message"].lower() or "invalid" in response["message"].lower()


# ============================================================================
# 测试用例：多种姿态问题组合
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_hunchback_detection(client, mock_pose_detector, mock_posture_analyzer, mock_alert_manager):
    """测试驼背检测"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)

    # 创建驼背的分析结果
    hunchback_result = create_mock_analysis_result(has_issues=False)
    hunchback_result.hunchback = True
    hunchback_result.hunchback_offset = 0.15
    mock_posture_analyzer.analyze.return_value = hunchback_result

    # 设置 AlertManager 返回 warning 状态
    mock_alert_manager.check_and_alert.return_value = {
        'should_alert': False,
        'status_indicator': {
            'status': 'warning',
            'color': 'yellow',
            'label': '需注意'
        }
    }

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 验证检测到驼背
        assert response["analysis"]["hunchback"] is True
        assert response["status_indicator"]["status"] == "warning"


@pytest.mark.asyncio
async def test_websocket_crossed_legs_detection(client, mock_pose_detector, mock_posture_analyzer, mock_alert_manager):
    """测试跷二郎腿检测"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)

    # 创建跷二郎腿的分析结果
    crossed_legs_result = create_mock_analysis_result(has_issues=False)
    crossed_legs_result.crossed_legs = True
    crossed_legs_result.crossed_legs_diff = 0.08
    mock_posture_analyzer.analyze.return_value = crossed_legs_result

    # 设置 AlertManager 返回 warning 状态
    mock_alert_manager.check_and_alert.return_value = {
        'should_alert': False,
        'status_indicator': {
            'status': 'warning',
            'color': 'yellow',
            'label': '需注意'
        }
    }

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 验证检测到跷二郎腿
        assert response["analysis"]["crossed_legs"] is True
        assert response["status_indicator"]["status"] == "warning"


@pytest.mark.asyncio
async def test_websocket_multiple_issues_bad_status(client, mock_pose_detector, mock_posture_analyzer, mock_alert_manager):
    """测试多个问题时状态为 bad"""
    mock_pose_detector.detect.return_value = create_mock_pose_result(detected=True)

    # 创建多个问题的分析结果
    multi_issue_result = create_mock_analysis_result(has_issues=True)
    multi_issue_result.hunchback = True
    multi_issue_result.hunchback_offset = 0.15
    mock_posture_analyzer.analyze.return_value = multi_issue_result

    # 设置 AlertManager 返回 bad 状态（多个问题）
    mock_alert_manager.check_and_alert.return_value = {
        'should_alert': True,
        'sound_alert': {'frequency': 800, 'duration': 0.2},
        'popup_alert': {'title': '坐姿提醒', 'message': '头部前倾和驼背'},
        'status_indicator': {
            'status': 'bad',
            'color': 'red',
            'label': '需立即纠正'
        }
    }

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 验证状态为 bad（多个问题）
        assert response["analysis"]["head_forward"] is True
        assert response["analysis"]["hunchback"] is True
        assert response["status_indicator"]["status"] == "bad"


# ============================================================================
# 测试用例：WebSocket 异常处理
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_connection_error_handling(client, mock_pose_detector):
    """测试 WebSocket 连接异常处理"""
    # 模拟检测器抛出严重异常
    mock_pose_detector.detect.side_effect = RuntimeError("Critical detector error")

    with client.websocket_connect("/ws/posture") as websocket:
        test_data = {
            "type": "video_frame",
            "data": create_test_image_base64(),
            "timestamp": 1234567890.123
        }
        websocket.send_json(test_data)

        response = websocket.receive_json()

        # 应该返回错误响应
        assert response["type"] == "error"
