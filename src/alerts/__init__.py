"""
提醒系统模块

提供坐姿监测的提醒功能，包括声音提醒、弹窗提醒和状态指示。

主要组件:
- AlertManager: 提醒管理器，协调所有提醒类型
- SoundAlert: 声音提醒生成器
- PopupAlert: 弹窗消息生成器
"""

from src.alerts.alert_manager import AlertManager
from src.alerts.sound_alert import SoundAlert
from src.alerts.popup_alert import PopupAlert

__all__ = [
    'AlertManager',
    'SoundAlert',
    'PopupAlert',
]

__version__ = '1.0.0'