"""
REST API 路由单元测试

测试历史记录、统计和设置 API 功能
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.models.posture_record import PostureRecord
from src.api.deps import get_db_session


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = AsyncMock()
    return session


@pytest.fixture
def client(mock_db_session):
    """创建测试客户端，并覆盖数据库依赖"""
    def override_get_db_session():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_record_service():
    """模拟 RecordService"""
    service = Mock()

    # 模拟 get_records
    mock_records = [
        PostureRecord(
            id=1,
            timestamp=datetime.now(),
            posture_type="head_forward",
            severity=0.8,
            duration_seconds=30.5
        ),
        PostureRecord(
            id=2,
            timestamp=datetime.now() - timedelta(hours=1),
            posture_type="hunchback",
            severity=0.6,
            duration_seconds=45.0
        )
    ]
    service.get_records = AsyncMock(return_value=mock_records)

    # 模拟 get_statistics
    service.get_statistics = AsyncMock(return_value={
        'total_records': 10,
        'posture_distribution': {
            'head_forward': 5,
            'hunchback': 3,
            'crossed_legs': 2
        },
        'avg_severity': 0.65,
        'total_duration': 300.0,
        'period_start': datetime.now() - timedelta(days=1),
        'period_end': datetime.now()
    })

    return service


# ============================================================================
# 测试用例：历史记录 API
# ============================================================================

@pytest.mark.asyncio
async def test_get_records_success(client, mock_record_service):
    """测试成功获取历史记录"""
    with patch('src.api.routes.records.RecordService', return_value=mock_record_service):
        response = client.get("/api/records")

        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert len(data["records"]) > 0


@pytest.mark.asyncio
async def test_get_records_with_filters(client, mock_record_service):
    """测试带过滤条件的历史记录查询"""
    with patch('src.api.routes.records.RecordService', return_value=mock_record_service):
        # 测试时间范围过滤
        response = client.get("/api/records", params={
            "start_time": "2026-01-14T00:00:00",
            "end_time": "2026-01-14T23:59:59",
            "posture_type": "head_forward",
            "limit": 50,
            "offset": 0
        })

        assert response.status_code == 200
        data = response.json()
        assert "records" in data


@pytest.mark.asyncio
async def test_get_records_invalid_posture_type(client):
    """测试无效的姿态类型"""
    response = client.get("/api/records", params={
        "posture_type": "invalid_type"
    })

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_records_invalid_time_range(client):
    """测试无效的时间范围"""
    response = client.get("/api/records", params={
        "start_time": "2026-01-14T23:59:59",
        "end_time": "2026-01-14T00:00:00"  # 结束时间早于开始时间
    })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_records_pagination(client, mock_record_service):
    """测试分页功能"""
    with patch('src.api.routes.records.RecordService', return_value=mock_record_service):
        # 第一页
        response = client.get("/api/records", params={
            "limit": 10,
            "offset": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

        # 第二页
        response = client.get("/api/records", params={
            "limit": 10,
            "offset": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2


# ============================================================================
# 测试用例：统计 API
# ============================================================================

@pytest.mark.asyncio
async def test_get_statistics_day(client, mock_record_service):
    """测试按日统计"""
    with patch('src.api.routes.statistics.RecordService', return_value=mock_record_service):
        response = client.get("/api/statistics", params={"period": "day"})

        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data
        assert "posture_distribution" in data
        assert "avg_severity" in data
        assert data["total_records"] == 10


@pytest.mark.asyncio
async def test_get_statistics_week(client, mock_record_service):
    """测试按周统计"""
    with patch('src.api.routes.statistics.RecordService', return_value=mock_record_service):
        response = client.get("/api/statistics", params={"period": "week"})

        assert response.status_code == 200
        data = response.json()
        assert data["posture_distribution"] == {
            'head_forward': 5,
            'hunchback': 3,
            'crossed_legs': 2
        }


@pytest.mark.asyncio
async def test_get_statistics_month(client, mock_record_service):
    """测试按月统计"""
    with patch('src.api.routes.statistics.RecordService', return_value=mock_record_service):
        response = client.get("/api/statistics", params={"period": "month"})

        assert response.status_code == 200
        data = response.json()
        assert data["avg_severity"] == 0.65
        assert data["total_duration"] == 300.0


@pytest.mark.asyncio
async def test_get_statistics_with_end_time(client, mock_record_service):
    """测试指定结束时间的统计"""
    with patch('src.api.routes.statistics.RecordService', return_value=mock_record_service):
        response = client.get("/api/statistics", params={
            "period": "day",
            "end_time": "2026-01-14T23:59:59"
        })

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_statistics_invalid_period(client):
    """测试无效的统计周期"""
    response = client.get("/api/statistics", params={"period": "invalid"})

    assert response.status_code == 422  # FastAPI 验证错误


# ============================================================================
# 测试用例：设置 API
# ============================================================================

def test_get_settings(client):
    """测试获取当前设置"""
    response = client.get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert "alert_settings" in data
    assert "detection_thresholds" in data
    assert "cooldown_seconds" in data["alert_settings"]
    assert "head_forward_angle" in data["detection_thresholds"]


def test_update_alert_settings(client):
    """测试更新提醒设置"""
    response = client.put("/api/settings", json={
        "alert_settings": {
            "cooldown_seconds": 60.0,
            "enable_sound": False,
            "enable_popup": True
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["settings"]["alert_settings"]["cooldown_seconds"] == 60.0
    assert data["settings"]["alert_settings"]["enable_sound"] is False


def test_update_detection_thresholds(client):
    """测试更新检测阈值"""
    response = client.put("/api/settings", json={
        "detection_thresholds": {
            "head_forward_angle": 20.0,
            "hunchback_offset": 0.15,
            "crossed_legs_diff": 0.08
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["settings"]["detection_thresholds"]["head_forward_angle"] == 20.0


def test_update_all_settings(client):
    """测试同时更新所有设置"""
    response = client.put("/api/settings", json={
        "alert_settings": {
            "cooldown_seconds": 45.0,
            "enable_sound": True,
            "enable_popup": True
        },
        "detection_thresholds": {
            "head_forward_angle": 18.0,
            "hunchback_offset": 0.12,
            "crossed_legs_diff": 0.06
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "alert_settings, detection_thresholds" in data["message"]


def test_update_settings_invalid_values(client):
    """测试无效的设置值"""
    # 冷却时间过小
    response = client.put("/api/settings", json={
        "alert_settings": {
            "cooldown_seconds": 1.0  # 小于最小值 5.0
        }
    })
    assert response.status_code == 422

    # 角度阈值超出范围
    response = client.put("/api/settings", json={
        "detection_thresholds": {
            "head_forward_angle": 100.0  # 大于最大值 45.0
        }
    })
    assert response.status_code == 422


def test_reset_settings(client):
    """测试重置设置到默认值"""
    # 先修改设置
    client.put("/api/settings", json={
        "alert_settings": {
            "cooldown_seconds": 60.0
        }
    })

    # 重置设置
    response = client.post("/api/settings/reset")

    assert response.status_code == 200
    data = response.json()
    assert data["alert_settings"]["cooldown_seconds"] == 30.0  # 默认值


# ============================================================================
# 测试用例：Schema 验证
# ============================================================================

def test_record_query_params_validation():
    """测试记录查询参数验证"""
    from src.api.schemas.records import RecordQueryParams

    # 有效参数
    params = RecordQueryParams(
        start_time=datetime.now() - timedelta(days=1),
        end_time=datetime.now(),
        posture_type="head_forward",
        limit=50,
        offset=0
    )
    assert params.limit == 50

    # 无效的 posture_type
    with pytest.raises(ValueError):
        RecordQueryParams(posture_type="invalid_type")

    # 无效的时间范围
    with pytest.raises(ValueError):
        RecordQueryParams(
            start_time=datetime.now(),
            end_time=datetime.now() - timedelta(days=1)
        )


def test_settings_schema_validation():
    """测试设置 Schema 验证"""
    from src.api.schemas.settings import AlertSettings, DetectionThresholds

    # 有效的提醒设置
    alert_settings = AlertSettings(
        cooldown_seconds=30.0,
        enable_sound=True,
        enable_popup=True
    )
    assert alert_settings.cooldown_seconds == 30.0

    # 有效的检测阈值
    thresholds = DetectionThresholds(
        head_forward_angle=15.0,
        hunchback_offset=0.1,
        crossed_legs_diff=0.05
    )
    assert thresholds.head_forward_angle == 15.0


# ============================================================================
# 测试用例：错误处理
# ============================================================================

@pytest.mark.asyncio
async def test_api_error_handling(client):
    """测试 API 错误处理"""
    # 模拟数据库错误
    error_service = Mock()
    error_service.get_records = AsyncMock(side_effect=Exception("Database error"))

    with patch('src.api.routes.records.RecordService', return_value=error_service):
        response = client.get("/api/records")

        assert response.status_code == 500
        assert "detail" in response.json()


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(client):
    """测试根路径端点（返回HTML主页）"""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "坐姿监测系统" in response.text


def test_api_info_endpoint(client):
    """测试API信息端点"""
    response = client.get("/api")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "endpoints" in data


# ============================================================================
# 测试用例：设置 API 错误处理
# ============================================================================

def test_get_settings_internal_error(client):
    """测试获取设置时的内部错误"""
    with patch('src.api.routes.settings.AlertSettings') as MockAlertSettings:
        # 模拟创建 AlertSettings 时抛出异常
        MockAlertSettings.side_effect = RuntimeError("Settings error")

        response = client.get("/api/settings")

        # 应该返回 500 错误
        assert response.status_code == 500
        assert "detail" in response.json()


def test_update_settings_value_error(client):
    """测试更新设置时的值错误"""
    # 尝试更新无效的值（超出范围）
    response = client.put("/api/settings", json={
        "alert_settings": {
            "cooldown_seconds": 500.0  # 超过最大值 300.0
        }
    })

    # 应该返回验证错误
    assert response.status_code == 422


def test_update_settings_internal_error(client):
    """测试更新设置时的内部错误"""
    with patch('src.api.routes.settings._current_settings', new={}):
        with patch('src.api.routes.settings.AlertSettings') as MockAlertSettings:
            # 模拟内部错误
            MockAlertSettings.side_effect = Exception("Internal error")

            response = client.put("/api/settings", json={
                "alert_settings": {
                    "cooldown_seconds": 30.0
                }
            })

            # 应该返回 500 错误
            assert response.status_code == 500
            assert "detail" in response.json()


def test_reset_settings_internal_error(client):
    """测试重置设置时的内部错误"""
    with patch('src.api.routes.settings.AlertSettings') as MockAlertSettings:
        # 模拟创建 AlertSettings 时抛出异常
        MockAlertSettings.side_effect = RuntimeError("Reset error")

        response = client.post("/api/settings/reset")

        # 应该返回 500 错误
        assert response.status_code == 500


# ============================================================================
# 测试用例：统计 API 错误处理
# ============================================================================

@pytest.mark.asyncio
async def test_get_statistics_value_error(client):
    """测试统计 API 的值错误处理"""
    with patch('src.api.routes.statistics.RecordService') as MockService:
        mock_service = Mock()
        # 模拟 get_statistics 抛出 ValueError
        mock_service.get_statistics = AsyncMock(side_effect=ValueError("Invalid period"))
        MockService.return_value = mock_service

        response = client.get("/api/statistics", params={"period": "day"})

        # 应该返回 400 错误
        assert response.status_code == 400
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_statistics_internal_error(client):
    """测试统计 API 的内部错误处理"""
    with patch('src.api.routes.statistics.RecordService') as MockService:
        mock_service = Mock()
        # 模拟 get_statistics 抛出通用异常
        mock_service.get_statistics = AsyncMock(side_effect=Exception("Database error"))
        MockService.return_value = mock_service

        response = client.get("/api/statistics", params={"period": "day"})

        # 应该返回 500 错误
        assert response.status_code == 500
        assert "detail" in response.json()
