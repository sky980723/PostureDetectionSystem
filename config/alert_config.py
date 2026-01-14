"""
提醒系统配置模块

定义提醒系统的各项配置参数，包括冷却时间、音频参数、提醒文案等。
"""

from typing import Dict, List


class AlertConfig:
    """提醒系统配置类"""

    # ==================== 冷却时间配置 ====================
    # 默认冷却时间（秒）- 避免频繁提醒
    DEFAULT_COOLDOWN_SECONDS = 30.0

    # 不同严重程度的冷却时间
    COOLDOWN_BY_SEVERITY = {
        'good': float('inf'),  # 正常状态不提醒
        'warning': 60.0,       # 警告级别 60 秒冷却
        'bad': 30.0            # 严重级别 30 秒冷却
    }

    # ==================== 状态栏指示配置 ====================
    STATUS_COLORS = {
        'good': 'green',
        'warning': 'yellow',
        'bad': 'red'
    }

    STATUS_LABELS = {
        'good': '坐姿良好',
        'warning': '坐姿欠佳',
        'bad': '坐姿不良'
    }

    # ==================== 声音提醒配置 ====================
    # 基础音频参数
    SOUND_PARAMS = {
        'warning': {
            'frequency': 440,      # Hz (A4音符)
            'duration': 0.3,       # 秒
            'volume': 0.5,         # 音量 0-1
            'wave_type': 'sine'    # 波形: sine, square, triangle, sawtooth
        },
        'bad': {
            'frequency': 880,      # Hz (A5音符，更高音)
            'duration': 0.5,       # 秒
            'volume': 0.7,         # 音量 0-1
            'wave_type': 'square'  # 方波更刺耳
        }
    }

    # ==================== 弹窗提醒配置 ====================
    # 问题类型对应的描述
    ISSUE_DESCRIPTIONS = {
        'head_forward': '头部前倾',
        'hunchback': '驼背',
        'crossed_legs': '跷二郎腿'
    }

    # 问题类型对应的建议
    ISSUE_SUGGESTIONS = {
        'head_forward': [
            '调整屏幕高度，使视线平视',
            '将头部向后收，保持颈椎自然曲线',
            '避免长时间低头'
        ],
        'hunchback': [
            '挺胸收腹，保持背部挺直',
            '调整椅背角度，提供腰部支撑',
            '每小时起身活动，放松背部肌肉'
        ],
        'crossed_legs': [
            '双脚平放在地面上',
            '膝盖与髋部保持同一高度',
            '避免长时间保持同一姿势'
        ]
    }

    # 弹窗标题
    POPUP_TITLES = {
        'warning': '坐姿提醒',
        'bad': '坐姿警告'
    }

    # ==================== 提醒触发条件 ====================
    # 需要连续检测到问题的次数才触发提醒
    TRIGGER_THRESHOLD = 3

    @classmethod
    def get_cooldown_time(cls, severity: str) -> float:
        """
        获取指定严重程度的冷却时间

        Args:
            severity: 严重程度 ('good', 'warning', 'bad')

        Returns:
            float: 冷却时间（秒）
        """
        return cls.COOLDOWN_BY_SEVERITY.get(
            severity,
            cls.DEFAULT_COOLDOWN_SECONDS
        )

    @classmethod
    def get_status_color(cls, status: str) -> str:
        """
        获取状态对应的颜色

        Args:
            status: 状态 ('good', 'warning', 'bad')

        Returns:
            str: 颜色代码
        """
        return cls.STATUS_COLORS.get(status, 'gray')

    @classmethod
    def get_status_label(cls, status: str) -> str:
        """
        获取状态对应的标签文本

        Args:
            status: 状态 ('good', 'warning', 'bad')

        Returns:
            str: 标签文本
        """
        return cls.STATUS_LABELS.get(status, '未知状态')

    @classmethod
    def get_sound_params(cls, severity: str) -> Dict:
        """
        获取声音提醒参数

        Args:
            severity: 严重程度 ('warning', 'bad')

        Returns:
            Dict: 音频参数字典
        """
        return cls.SOUND_PARAMS.get(severity, cls.SOUND_PARAMS['warning'])

    @classmethod
    def get_issue_description(cls, issue_type: str) -> str:
        """
        获取问题类型的描述

        Args:
            issue_type: 问题类型

        Returns:
            str: 问题描述
        """
        return cls.ISSUE_DESCRIPTIONS.get(issue_type, issue_type)

    @classmethod
    def get_issue_suggestions(cls, issue_type: str) -> List[str]:
        """
        获取问题类型的改进建议

        Args:
            issue_type: 问题类型

        Returns:
            List[str]: 建议列表
        """
        return cls.ISSUE_SUGGESTIONS.get(issue_type, [])
