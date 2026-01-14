"""
声音提醒模块

生成适用于 Web Audio API 的音频参数，用于播放提醒音效。
"""

from typing import Dict, Optional
from config.alert_config import AlertConfig


class SoundAlert:
    """
    声音提醒类

    生成用于 Web Audio API 的音频参数。
    不直接播放音频，而是返回参数供前端 JavaScript 使用。
    """

    def __init__(self):
        """初始化声音提醒类"""
        pass

    def generate_alert_params(
        self,
        severity: str = 'warning'
    ) -> Dict[str, any]:
        """
        生成提醒音频参数

        根据严重程度返回不同的音频配置，供前端 Web Audio API 使用。

        Args:
            severity: 严重程度 ('warning' 或 'bad')
                - 'warning': 温和提醒音（低频、短时长）
                - 'bad': 紧急警告音（高频、长时长）

        Returns:
            Dict: 音频参数字典，包含:
                - frequency: int - 频率（Hz）
                - duration: float - 时长（秒）
                - volume: float - 音量（0-1）
                - wave_type: str - 波形类型
                - pattern: Optional[List] - 音符序列（用于复杂音效）
        """
        # 获取基础配置
        sound_config = AlertConfig.get_sound_params(severity)

        # 构建音频参数
        params = {
            'frequency': sound_config['frequency'],
            'duration': sound_config['duration'],
            'volume': sound_config['volume'],
            'wave_type': sound_config['wave_type']
        }

        # 根据严重程度添加音符模式
        if severity == 'bad':
            # 紧急提醒使用双音节模式（beep-beep）
            params['pattern'] = [
                {'frequency': sound_config['frequency'], 'duration': 0.2},
                {'frequency': 0, 'duration': 0.1},  # 静音间隔
                {'frequency': sound_config['frequency'], 'duration': 0.2}
            ]
        else:
            # 警告提醒使用单音节
            params['pattern'] = [
                {'frequency': sound_config['frequency'], 'duration': sound_config['duration']}
            ]

        return params

    def get_sound_config(self, severity: str) -> Dict[str, any]:
        """
        获取指定严重程度的声音配置

        这是一个便捷方法，直接返回配置文件中的参数。

        Args:
            severity: 严重程度 ('warning' 或 'bad')

        Returns:
            Dict: 声音配置字典
        """
        return AlertConfig.get_sound_params(severity)

    @staticmethod
    def create_custom_alert(
        frequency: int,
        duration: float,
        volume: float = 0.5,
        wave_type: str = 'sine'
    ) -> Dict[str, any]:
        """
        创建自定义音频提醒参数

        允许完全自定义音频参数，用于特殊场景。

        Args:
            frequency: 频率（Hz），典型范围 200-2000
            duration: 时长（秒），建议 0.1-1.0
            volume: 音量（0-1），建议 0.3-0.7
            wave_type: 波形类型 ('sine', 'square', 'triangle', 'sawtooth')

        Returns:
            Dict: 自定义音频参数字典

        Raises:
            ValueError: 参数超出有效范围时抛出
        """
        # 参数验证
        if not 20 <= frequency <= 20000:
            raise ValueError(f"频率 {frequency} Hz 超出有效范围 (20-20000 Hz)")

        if not 0.05 <= duration <= 5.0:
            raise ValueError(f"时长 {duration}s 超出有效范围 (0.05-5.0s)")

        if not 0.0 <= volume <= 1.0:
            raise ValueError(f"音量 {volume} 超出有效范围 (0.0-1.0)")

        valid_wave_types = ['sine', 'square', 'triangle', 'sawtooth']
        if wave_type not in valid_wave_types:
            raise ValueError(
                f"无效的波形类型 '{wave_type}'，"
                f"有效值: {', '.join(valid_wave_types)}"
            )

        return {
            'frequency': frequency,
            'duration': duration,
            'volume': volume,
            'wave_type': wave_type,
            'pattern': [{'frequency': frequency, 'duration': duration}]
        }

    @staticmethod
    def create_multi_tone_alert(
        frequencies: list,
        durations: list,
        volume: float = 0.5,
        wave_type: str = 'sine'
    ) -> Dict[str, any]:
        """
        创建多音调提醒（例如：do-re-mi 音阶）

        Args:
            frequencies: 频率列表（Hz）
            durations: 时长列表（秒），需要与 frequencies 长度一致
            volume: 音量（0-1）
            wave_type: 波形类型

        Returns:
            Dict: 多音调音频参数字典

        Raises:
            ValueError: 参数列表长度不一致时抛出
        """
        if len(frequencies) != len(durations):
            raise ValueError(
                f"频率列表长度 ({len(frequencies)}) "
                f"与时长列表长度 ({len(durations)}) 不一致"
            )

        pattern = []
        total_duration = 0

        for freq, dur in zip(frequencies, durations):
            pattern.append({'frequency': freq, 'duration': dur})
            total_duration += dur

        return {
            'frequency': frequencies[0],  # 主频率（第一个音符）
            'duration': total_duration,
            'volume': volume,
            'wave_type': wave_type,
            'pattern': pattern
        }
