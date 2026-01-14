"""
依赖注入单元测试

测试 FastAPI 依赖注入函数
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.api.deps import (
    get_db_session,
    get_record_service,
    get_pose_detector,
    get_posture_analyzer,
    get_alert_manager,
    cleanup_detector
)


# ============================================================================
# 测试用例：数据库会话依赖
# ============================================================================

@pytest.mark.asyncio
async def test_get_db_session():
    """测试数据库会话依赖注入"""
    with patch('src.api.deps.get_session') as mock_get_session:
        # 模拟异步生成器
        async def mock_session_generator():
            yield AsyncMock()

        mock_get_session.return_value = mock_session_generator()

        # 测试获取会话
        async for session in get_db_session():
            assert session is not None
            break


# ============================================================================
# 测试用例：RecordService 依赖
# ============================================================================

@pytest.mark.asyncio
async def test_get_record_service_with_session():
    """测试传入 session 参数时的 RecordService 获取"""
    mock_session = AsyncMock()

    with patch('src.api.deps.RecordService') as MockRecordService:
        mock_service = Mock()
        MockRecordService.return_value = mock_service

        # 传入 session
        service = await get_record_service(session=mock_session)

        assert service is not None
        MockRecordService.assert_called_once_with(mock_session)


@pytest.mark.asyncio
async def test_get_record_service_without_session():
    """测试不传入 session 参数时的 RecordService 获取"""
    with patch('src.api.deps.get_db_session') as mock_get_db:
        with patch('src.api.deps.RecordService') as MockRecordService:
            # 模拟数据库会话生成器
            async def mock_session_generator():
                yield AsyncMock()

            mock_get_db.return_value = mock_session_generator()
            mock_service = Mock()
            MockRecordService.return_value = mock_service

            # 不传入 session（使用默认值 None）
            service = await get_record_service(session=None)

            assert service is not None


# ============================================================================
# 测试用例：PoseDetector 单例模式
# ============================================================================

def test_get_pose_detector_singleton():
    """测试 PoseDetector 单例模式"""
    # 清理可能存在的实例
    if hasattr(get_pose_detector, '_instance'):
        delattr(get_pose_detector, '_instance')

    with patch('src.api.deps.PoseDetector') as MockDetector:
        mock_instance = Mock()
        MockDetector.return_value = mock_instance

        # 第一次调用：创建实例
        detector1 = get_pose_detector()
        assert detector1 == mock_instance
        MockDetector.assert_called_once()

        # 第二次调用：返回缓存的实例
        detector2 = get_pose_detector()
        assert detector2 == detector1
        # 确认没有再次创建实例
        assert MockDetector.call_count == 1

    # 清理
    if hasattr(get_pose_detector, '_instance'):
        delattr(get_pose_detector, '_instance')


# ============================================================================
# 测试用例：PostureAnalyzer 单例模式
# ============================================================================

def test_get_posture_analyzer_singleton():
    """测试 PostureAnalyzer 单例模式"""
    # 清理可能存在的实例
    if hasattr(get_posture_analyzer, '_instance'):
        delattr(get_posture_analyzer, '_instance')

    with patch('src.api.deps.PostureAnalyzer') as MockAnalyzer:
        mock_instance = Mock()
        MockAnalyzer.return_value = mock_instance

        # 第一次调用：创建实例
        analyzer1 = get_posture_analyzer()
        assert analyzer1 == mock_instance
        MockAnalyzer.assert_called_once()

        # 第二次调用：返回缓存的实例
        analyzer2 = get_posture_analyzer()
        assert analyzer2 == analyzer1
        # 确认没有再次创建实例
        assert MockAnalyzer.call_count == 1

    # 清理
    if hasattr(get_posture_analyzer, '_instance'):
        delattr(get_posture_analyzer, '_instance')


# ============================================================================
# 测试用例：AlertManager 依赖
# ============================================================================

def test_get_alert_manager():
    """测试 AlertManager 依赖注入（每次创建新实例）"""
    with patch('src.api.deps.AlertManager') as MockAlertManager:
        mock_instance1 = Mock()
        mock_instance2 = Mock()
        MockAlertManager.side_effect = [mock_instance1, mock_instance2]

        # 第一次调用
        manager1 = get_alert_manager()
        assert manager1 == mock_instance1

        # 第二次调用：应该创建新实例（不是单例）
        manager2 = get_alert_manager()
        assert manager2 == mock_instance2
        assert manager1 != manager2

        # 确认调用了两次
        assert MockAlertManager.call_count == 2


# ============================================================================
# 测试用例：资源清理
# ============================================================================

def test_cleanup_detector_with_instance():
    """测试清理 PoseDetector 实例"""
    # 创建一个模拟实例
    mock_instance = Mock()
    mock_instance.close = Mock()
    get_pose_detector._instance = mock_instance

    # 执行清理
    cleanup_detector()

    # 验证 close 被调用
    mock_instance.close.assert_called_once()

    # 验证实例被删除
    assert not hasattr(get_pose_detector, '_instance')


def test_cleanup_detector_without_instance():
    """测试在没有实例时清理"""
    # 确保没有实例
    if hasattr(get_pose_detector, '_instance'):
        delattr(get_pose_detector, '_instance')

    # 执行清理（不应该抛出异常）
    cleanup_detector()

    # 验证没有实例
    assert not hasattr(get_pose_detector, '_instance')
