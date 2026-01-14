"""
提醒管理器模块

负责协调所有提醒类型，管理提醒冷却时间，并决定何时触发提醒。
"""

import time
from typing import Dict, List, Optional, Any
from config.alert_config import AlertConfig


class AlertManager:
    """
    提醒管理器类

    负责检查坐姿状态并触发相应的提醒，支持多种提醒类型同时触发。
    实现了提醒冷却机制，避免频繁打扰用户。
    """

    def __init__(
        self,
        cooldown_seconds: Optional[float] = None,
        enable_sound: bool = True,
        enable_popup: bool = True
    ):
        """
        初始化提醒管理器

        Args:
            cooldown_seconds: 自定义冷却时间（秒），None 则使用配置的默认值
            enable_sound: 是否启用声音提醒
            enable_popup: 是否启用弹窗提醒
        """
        self.default_cooldown = (
            cooldown_seconds
            if cooldown_seconds is not None
            else AlertConfig.DEFAULT_COOLDOWN_SECONDS
        )
        # 标记是否使用了自定义冷却时间
        self._use_custom_cooldown = cooldown_seconds is not None
        self.enable_sound = enable_sound
        self.enable_popup = enable_popup

        # 上次提醒的时间戳
        self._last_alert_time: Optional[float] = None

        # 上次提醒的严重程度
        self._last_severity: Optional[str] = None

        # 连续检测到问题的计数器
        self._consecutive_issues_count = 0

        # 上次检测到的问题类型
        self._last_issues: List[str] = []

    def check_and_alert(self, posture_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查姿态状态并触发提醒

        根据姿态状态决定是否需要触发提醒，并返回提醒信息。
        实现了冷却时间和连续检测阈值机制。

        Args:
            posture_state: 姿态状态字典，包含以下字段:
                - status: 'good' | 'warning' | 'bad'
                - issues: List[str] - 检测到的问题列表
                - angles: Dict - 角度数据（可选）
                - timestamp: float - 时间戳（可选）

        Returns:
            Dict: 提醒信息字典，包含以下字段:
                - should_alert: bool - 是否应该触发提醒
                - sound_alert: Optional[Dict] - 声音提醒参数
                - popup_alert: Optional[Dict] - 弹窗提醒内容
                - status_indicator: Dict - 状态栏指示信息
        """
        current_time = time.time()
        status = posture_state.get('status', 'good')
        issues = posture_state.get('issues', [])

        # 更新连续问题计数
        self._update_consecutive_count(status, issues)

        # 构建返回结果
        result = {
            'should_alert': False,
            'sound_alert': None,
            'popup_alert': None,
            'status_indicator': self.get_status_indicator(status)
        }

        # 如果状态良好，重置计数器，不触发提醒
        if status == 'good':
            self._consecutive_issues_count = 0
            self._last_issues = []
            return result

        # 检查是否满足触发条件
        if not self._should_alert(status, current_time):
            return result

        # 触发提醒
        result['should_alert'] = True

        # 生成声音提醒
        if self.enable_sound:
            from src.alerts.sound_alert import SoundAlert
            sound_alert = SoundAlert()
            result['sound_alert'] = sound_alert.generate_alert_params(status)

        # 生成弹窗提醒
        if self.enable_popup:
            from src.alerts.popup_alert import PopupAlert
            popup_alert = PopupAlert()
            result['popup_alert'] = popup_alert.generate_message(posture_state)

        # 更新上次提醒时间和严重程度
        self._last_alert_time = current_time
        self._last_severity = status

        return result

    def _should_alert(self, severity: str, current_time: float) -> bool:
        """
        判断是否应该触发提醒

        考虑以下因素:
        1. 连续检测阈值 - 需要连续检测到问题才触发
        2. 冷却时间 - 避免频繁提醒

        Args:
            severity: 严重程度 ('warning', 'bad')
            current_time: 当前时间戳

        Returns:
            bool: 是否应该触发提醒
        """
        # 检查连续检测阈值
        if self._consecutive_issues_count < AlertConfig.TRIGGER_THRESHOLD:
            return False

        # 如果从未提醒过，直接触发
        if self._last_alert_time is None:
            return True

        # 获取冷却时间
        if self._use_custom_cooldown:
            # 使用自定义冷却时间
            cooldown_time = self.default_cooldown
        else:
            # 根据严重程度获取配置的冷却时间
            cooldown_time = AlertConfig.get_cooldown_time(severity)

        # 检查冷却时间
        time_since_last_alert = current_time - self._last_alert_time

        # 如果严重程度升级（从 warning 到 bad），缩短冷却时间
        if self._last_severity == 'warning' and severity == 'bad':
            cooldown_time = cooldown_time * 0.5  # 缩短一半

        return time_since_last_alert >= cooldown_time

    def _update_consecutive_count(self, status: str, issues: List[str]) -> None:
        """
        更新连续检测到问题的计数器

        Args:
            status: 当前状态
            issues: 当前检测到的问题列表
        """
        # 如果问题类型与上次相同，增加计数
        if status != 'good' and set(issues) == set(self._last_issues):
            self._consecutive_issues_count += 1
        else:
            # 如果问题类型变化或状态变好，重置计数
            self._consecutive_issues_count = 1 if status != 'good' else 0

        self._last_issues = issues

    def get_status_indicator(self, status: str) -> Dict[str, str]:
        """
        获取状态栏指示信息

        Args:
            status: 状态 ('good', 'warning', 'bad')

        Returns:
            Dict: 状态指示信息，包含:
                - status: str - 状态值
                - color: str - 颜色代码
                - label: str - 标签文本
        """
        return {
            'status': status,
            'color': AlertConfig.get_status_color(status),
            'label': AlertConfig.get_status_label(status)
        }

    def reset(self) -> None:
        """
        重置提醒管理器状态

        清除所有计数器和上次提醒时间，用于测试或重新开始监测。
        """
        self._last_alert_time = None
        self._last_severity = None
        self._consecutive_issues_count = 0
        self._last_issues = []

    def get_time_until_next_alert(self) -> Optional[float]:
        """
        获取距离下次可以提醒的时间

        Returns:
            Optional[float]: 剩余冷却时间（秒），None 表示可以立即提醒
        """
        if self._last_alert_time is None or self._last_severity is None:
            return None

        current_time = time.time()

        # 获取冷却时间
        if self._use_custom_cooldown:
            # 使用自定义冷却时间
            cooldown_time = self.default_cooldown
        else:
            # 根据严重程度获取配置的冷却时间
            cooldown_time = AlertConfig.get_cooldown_time(self._last_severity)

        time_since_last = current_time - self._last_alert_time
        remaining = cooldown_time - time_since_last

        return max(0, remaining) if remaining > 0 else None
