"""
API 配置管理

管理 FastAPI 应用的配置参数
"""

from pydantic_settings import BaseSettings
from typing import List


class APISettings(BaseSettings):
    """
    API 配置类

    支持通过环境变量覆盖（API_ 前缀）
    """
    # 应用配置
    app_name: str = "Posture Detection API"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS 配置
    cors_origins: List[str] = [
        "http://localhost:5173",  # Vite 开发服务器
        "http://localhost:3000",  # React 开发服务器（备选）
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # WebSocket 配置
    ws_max_connections: int = 10
    ws_heartbeat_interval: float = 30.0  # 秒
    ws_frame_rate_limit: float = 10.0  # 每秒最多处理的帧数

    # 数据库配置（复用现有配置）
    database_url: str = "sqlite+aiosqlite:///data/posture.db"

    # 提醒设置（默认值）
    default_cooldown_seconds: float = 30.0
    default_enable_sound: bool = True
    default_enable_popup: bool = True

    # 检测阈值（默认值，复用 settings.py 的配置）
    default_head_forward_angle: float = 15.0
    default_hunchback_offset: float = 0.1
    default_crossed_legs_diff: float = 0.05

    class Config:
        env_prefix = "API_"
        case_sensitive = False


# 创建全局配置实例
api_settings = APISettings()
