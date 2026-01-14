"""
FastAPI 依赖注入

提供数据库会话、服务实例等依赖
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_session
from src.storage.record_service import RecordService
from src.detectors.pose_detector import PoseDetector
from src.analyzers.posture_analyzer import PostureAnalyzer
from src.alerts.alert_manager import AlertManager
from config.api_settings import api_settings


# ============================================================================
# 数据库会话依赖
# ============================================================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数

    Yields:
        AsyncSession: 异步数据库会话
    """
    async for session in get_session():
        yield session


# ============================================================================
# 服务依赖
# ============================================================================

async def get_record_service(
    session: AsyncSession = None
) -> RecordService:
    """
    获取 RecordService 实例

    Args:
        session: 数据库会话（由 FastAPI 依赖注入）

    Returns:
        RecordService 实例
    """
    # 如果没有传入 session，使用 get_db_session
    if session is None:
        async for db_session in get_db_session():
            return RecordService(db_session)
    return RecordService(session)


def get_pose_detector() -> PoseDetector:
    """
    获取 PoseDetector 实例（单例模式）

    Returns:
        PoseDetector 实例
    """
    # 使用懒加载和缓存
    if not hasattr(get_pose_detector, '_instance'):
        get_pose_detector._instance = PoseDetector()
    return get_pose_detector._instance


def get_posture_analyzer() -> PostureAnalyzer:
    """
    获取 PostureAnalyzer 实例（单例模式）

    Returns:
        PostureAnalyzer 实例
    """
    if not hasattr(get_posture_analyzer, '_instance'):
        get_posture_analyzer._instance = PostureAnalyzer()
    return get_posture_analyzer._instance


def get_alert_manager() -> AlertManager:
    """
    获取 AlertManager 实例（每个连接独立）

    Returns:
        AlertManager 实例
    """
    return AlertManager(
        cooldown_seconds=api_settings.default_cooldown_seconds,
        enable_sound=api_settings.default_enable_sound,
        enable_popup=api_settings.default_enable_popup
    )


# ============================================================================
# 清理资源
# ============================================================================

def cleanup_detector():
    """清理 PoseDetector 资源"""
    if hasattr(get_pose_detector, '_instance'):
        get_pose_detector._instance.close()
        delattr(get_pose_detector, '_instance')
