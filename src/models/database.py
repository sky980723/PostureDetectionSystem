"""
数据库连接和配置模块

使用 SQLAlchemy 2.0 异步 API 提供数据库连接和会话管理
"""

import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

# 创建声明式基类
Base = declarative_base()

# 全局引擎和会话工厂
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url(db_path: str | None = None) -> str:
    """
    获取数据库 URL

    Args:
        db_path: 数据库文件路径，如果为 None 则使用默认路径

    Returns:
        数据库 URL 字符串
    """
    if db_path is None:
        # 默认数据库路径
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        db_path = str(data_dir / "posture.db")

    # SQLite 异步引擎使用 aiosqlite 驱动
    # 格式: sqlite+aiosqlite:///path/to/db.db
    return f"sqlite+aiosqlite:///{db_path}"


async def init_db(db_path: str | None = None, echo: bool = False) -> AsyncEngine:
    """
    初始化数据库引擎和会话工厂

    Args:
        db_path: 数据库文件路径，如果为 None 则使用默认路径
        echo: 是否打印 SQL 语句（用于调试）

    Returns:
        异步引擎实例
    """
    global _engine, _session_factory

    database_url = get_database_url(db_path)

    # 创建异步引擎
    _engine = create_async_engine(
        database_url,
        echo=echo,
        # SQLite 特定配置
        connect_args={"check_same_thread": False},
    )

    # 创建会话工厂
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,  # 避免在 commit 后对象失效
    )

    # 创建所有表
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（用于依赖注入）

    Yields:
        AsyncSession: 数据库会话实例

    Raises:
        RuntimeError: 如果数据库未初始化
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """
    关闭数据库连接
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
