"""
提醒系统单元测试

测试 AlertManager, SoundAlert, PopupAlert 的所有功能。
目标覆盖率: ≥90%
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.alerts.alert_manager import AlertManager
from src.alerts.sound_alert import SoundAlert
from src.alerts.popup_alert import PopupAlert
from config.alert_config import AlertConfig


# ==================== AlertManager 测试 ====================

class TestAlertManager:
    """AlertManager 类的测试套件"""

    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        manager = AlertManager()
        assert manager.default_cooldown == AlertConfig.DEFAULT_COOLDOWN_SECONDS
        assert manager.enable_sound is True
        assert manager.enable_popup is True
        assert manager._last_alert_time is None
        assert manager._consecutive_issues_count == 0

    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        manager = AlertManager(
            cooldown_seconds=60.0,
            enable_sound=False,
            enable_popup=True
        )
        assert manager.default_cooldown == 60.0
        assert manager.enable_sound is False
        assert manager.enable_popup is True

    def test_check_and_alert_good_status(self):
        """测试良好状态不触发提醒"""
        manager = AlertManager()
        posture_state = {
            'status': 'good',
            'issues': [],
            'timestamp': time.time()
        }

        result = manager.check_and_alert(posture_state)

        assert result['should_alert'] is False
        assert result['sound_alert'] is None
        assert result['popup_alert'] is None
        assert result['status_indicator']['status'] == 'good'
        assert result['status_indicator']['color'] == 'green'

    def test_check_and_alert_warning_below_threshold(self):
        """测试警告状态但未达到连续检测阈值"""
        manager = AlertManager()
        posture_state = {
            'status': 'warning',
            'issues': ['head_forward'],
            'timestamp': time.time()
        }

        # 第一次检测，连续计数为 1
        result = manager.check_and_alert(posture_state)
        assert result['should_alert'] is False

        # 第二次检测，连续计数为 2
        result = manager.check_and_alert(posture_state)
        assert result['should_alert'] is False

    def test_check_and_alert_warning_reaches_threshold(self):
        """测试警告状态达到连续检测阈值触发提醒"""
        manager = AlertManager()
        posture_state = {
            'status': 'warning',
            'issues': ['head_forward'],
            'timestamp': time.time()
        }

        # 触发阈值次数的检测
        for i in range(AlertConfig.TRIGGER_THRESHOLD - 1):
            result = manager.check_and_alert(posture_state)
            assert result['should_alert'] is False

        # 达到阈值，应该触发提醒
        result = manager.check_and_alert(posture_state)
        assert result['should_alert'] is True
        assert result['sound_alert'] is not None
        assert result['popup_alert'] is not None
        assert result['status_indicator']['status'] == 'warning'

    def test_check_and_alert_cooldown_mechanism(self):
        """测试冷却时间机制"""
        manager = AlertManager(cooldown_seconds=5.0)
        posture_state = {
            'status': 'warning',
            'issues': ['head_forward'],
            'timestamp': time.time()
        }

        # 先触发一次提醒
        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            manager.check_and_alert(posture_state)

        # 立即再次检查，应该被冷却时间阻止
        result = manager.check_and_alert(posture_state)
        assert result['should_alert'] is False

        # 手动修改_last_alert_time，模拟冷却时间过后
        manager._last_alert_time = time.time() - 6.0  # 假装6秒前触发的
        result = manager.check_and_alert(posture_state)
        assert result['should_alert'] is True

    def test_check_and_alert_severity_upgrade(self):
        """测试严重程度升级缩短冷却时间"""
        manager = AlertManager()

        # 先触发 warning 提醒
        warning_state = {
            'status': 'warning',
            'issues': ['head_forward'],
            'timestamp': time.time()
        }
        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            manager.check_and_alert(warning_state)

        # 升级到 bad 状态
        bad_state = {
            'status': 'bad',
            'issues': ['hunchback'],
            'timestamp': time.time()
        }

        # 手动修改_last_alert_time，模拟时间过去了16秒
        # bad 状态的冷却时间是 30 秒，升级后缩短一半为 15 秒
        manager._last_alert_time = time.time() - 16.0
        # 循环累积consecutive_count，第3次应该触发
        result = None
        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            result = manager.check_and_alert(bad_state)
        # 第3次循环时，consecutive_count达到阈值且过了缩短后的冷却时间，应该触发
        assert result['should_alert'] is True

    def test_consecutive_count_reset_on_status_change(self):
        """测试状态改变时连续计数重置"""
        manager = AlertManager()

        # 先检测到 warning
        warning_state = {
            'status': 'warning',
            'issues': ['head_forward']
        }
        for _ in range(2):
            manager.check_and_alert(warning_state)

        assert manager._consecutive_issues_count == 2

        # 状态变为 good
        good_state = {'status': 'good', 'issues': []}
        manager.check_and_alert(good_state)
        assert manager._consecutive_issues_count == 0

    def test_consecutive_count_reset_on_issue_change(self):
        """测试问题类型改变时连续计数重置"""
        manager = AlertManager()

        # 先检测到一种问题
        state1 = {'status': 'warning', 'issues': ['head_forward']}
        for _ in range(2):
            manager.check_and_alert(state1)

        assert manager._consecutive_issues_count == 2

        # 问题类型改变
        state2 = {'status': 'warning', 'issues': ['hunchback']}
        manager.check_and_alert(state2)
        assert manager._consecutive_issues_count == 1

    def test_get_status_indicator(self):
        """测试获取状态指示信息"""
        manager = AlertManager()

        # 测试各种状态
        indicators = {
            'good': {'status': 'good', 'color': 'green', 'label': '坐姿良好'},
            'warning': {'status': 'warning', 'color': 'yellow', 'label': '坐姿欠佳'},
            'bad': {'status': 'bad', 'color': 'red', 'label': '坐姿不良'}
        }

        for status, expected in indicators.items():
            result = manager.get_status_indicator(status)
            assert result == expected

    def test_reset(self):
        """测试重置功能"""
        manager = AlertManager()

        # 先触发一些状态
        state = {'status': 'warning', 'issues': ['head_forward']}
        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            manager.check_and_alert(state)

        # 重置
        manager.reset()
        assert manager._last_alert_time is None
        assert manager._last_severity is None
        assert manager._consecutive_issues_count == 0
        assert manager._last_issues == []

    def test_get_time_until_next_alert_none_when_no_previous(self):
        """测试从未提醒过时返回 None"""
        manager = AlertManager()
        assert manager.get_time_until_next_alert() is None

    def test_get_time_until_next_alert_remaining_time(self):
        """测试获取剩余冷却时间"""
        manager = AlertManager(cooldown_seconds=30.0)

        # 触发一次提醒
        state = {'status': 'warning', 'issues': ['head_forward']}
        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            manager.check_and_alert(state)

        # 模拟时间过去了 10 秒
        with patch('time.time') as mock_time:
            mock_time.return_value = manager._last_alert_time + 10.0
            remaining = manager.get_time_until_next_alert()
            # 使用自定义冷却时间 30 秒
            expected_remaining = 30.0 - 10.0
            assert abs(remaining - expected_remaining) < 0.1

    def test_get_time_until_next_alert_ready(self):
        """测试冷却时间过后返回 None"""
        manager = AlertManager()

        # 触发一次提醒
        state = {'status': 'warning', 'issues': ['head_forward']}
        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            manager.check_and_alert(state)

        # 模拟冷却时间已过
        with patch('time.time') as mock_time:
            mock_time.return_value = manager._last_alert_time + 100.0
            remaining = manager.get_time_until_next_alert()
            assert remaining is None

    def test_disabled_sound_alert(self):
        """测试禁用声音提醒"""
        manager = AlertManager(enable_sound=False)
        state = {'status': 'warning', 'issues': ['head_forward']}

        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            result = manager.check_and_alert(state)

        assert result['should_alert'] is True
        assert result['sound_alert'] is None
        assert result['popup_alert'] is not None

    def test_disabled_popup_alert(self):
        """测试禁用弹窗提醒"""
        manager = AlertManager(enable_popup=False)
        state = {'status': 'warning', 'issues': ['head_forward']}

        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            result = manager.check_and_alert(state)

        assert result['should_alert'] is True
        assert result['sound_alert'] is not None
        assert result['popup_alert'] is None


# ==================== SoundAlert 测试 ====================

class TestSoundAlert:
    """SoundAlert 类的测试套件"""

    def test_generate_alert_params_warning(self):
        """测试生成警告级别音频参数"""
        sound = SoundAlert()
        params = sound.generate_alert_params('warning')

        assert params['frequency'] == 440
        assert params['duration'] == 0.3
        assert params['volume'] == 0.5
        assert params['wave_type'] == 'sine'
        assert len(params['pattern']) == 1
        assert params['pattern'][0]['frequency'] == 440

    def test_generate_alert_params_bad(self):
        """测试生成严重级别音频参数"""
        sound = SoundAlert()
        params = sound.generate_alert_params('bad')

        assert params['frequency'] == 880
        assert params['duration'] == 0.5
        assert params['volume'] == 0.7
        assert params['wave_type'] == 'square'
        assert len(params['pattern']) == 3  # beep-pause-beep
        assert params['pattern'][1]['frequency'] == 0  # 静音间隔

    def test_get_sound_config_warning(self):
        """测试获取警告配置"""
        sound = SoundAlert()
        config = sound.get_sound_config('warning')

        assert config['frequency'] == 440
        assert config['duration'] == 0.3

    def test_get_sound_config_bad(self):
        """测试获取严重配置"""
        sound = SoundAlert()
        config = sound.get_sound_config('bad')

        assert config['frequency'] == 880
        assert config['duration'] == 0.5

    def test_create_custom_alert_valid_params(self):
        """测试创建自定义音频参数（有效参数）"""
        params = SoundAlert.create_custom_alert(
            frequency=500,
            duration=0.4,
            volume=0.6,
            wave_type='triangle'
        )

        assert params['frequency'] == 500
        assert params['duration'] == 0.4
        assert params['volume'] == 0.6
        assert params['wave_type'] == 'triangle'
        assert len(params['pattern']) == 1

    def test_create_custom_alert_invalid_frequency(self):
        """测试创建自定义音频参数（无效频率）"""
        with pytest.raises(ValueError, match="频率.*超出有效范围"):
            SoundAlert.create_custom_alert(frequency=25000, duration=0.5)

        with pytest.raises(ValueError, match="频率.*超出有效范围"):
            SoundAlert.create_custom_alert(frequency=10, duration=0.5)

    def test_create_custom_alert_invalid_duration(self):
        """测试创建自定义音频参数（无效时长）"""
        with pytest.raises(ValueError, match="时长.*超出有效范围"):
            SoundAlert.create_custom_alert(frequency=440, duration=10.0)

        with pytest.raises(ValueError, match="时长.*超出有效范围"):
            SoundAlert.create_custom_alert(frequency=440, duration=0.01)

    def test_create_custom_alert_invalid_volume(self):
        """测试创建自定义音频参数（无效音量）"""
        with pytest.raises(ValueError, match="音量.*超出有效范围"):
            SoundAlert.create_custom_alert(frequency=440, duration=0.5, volume=1.5)

        with pytest.raises(ValueError, match="音量.*超出有效范围"):
            SoundAlert.create_custom_alert(frequency=440, duration=0.5, volume=-0.1)

    def test_create_custom_alert_invalid_wave_type(self):
        """测试创建自定义音频参数（无效波形）"""
        with pytest.raises(ValueError, match="无效的波形类型"):
            SoundAlert.create_custom_alert(
                frequency=440,
                duration=0.5,
                wave_type='invalid'
            )

    def test_create_multi_tone_alert_valid(self):
        """测试创建多音调提醒（有效参数）"""
        frequencies = [262, 330, 392]  # C, E, G 和弦
        durations = [0.2, 0.2, 0.2]

        params = SoundAlert.create_multi_tone_alert(
            frequencies=frequencies,
            durations=durations,
            volume=0.5,
            wave_type='sine'
        )

        assert params['frequency'] == 262
        assert params['duration'] == pytest.approx(0.6, rel=1e-9)  # 总时长，使用pytest.approx处理浮点精度
        assert params['volume'] == 0.5
        assert len(params['pattern']) == 3
        assert params['pattern'][0]['frequency'] == 262
        assert params['pattern'][1]['frequency'] == 330
        assert params['pattern'][2]['frequency'] == 392

    def test_create_multi_tone_alert_length_mismatch(self):
        """测试创建多音调提醒（列表长度不匹配）"""
        with pytest.raises(ValueError, match="频率列表长度.*与时长列表长度.*不一致"):
            SoundAlert.create_multi_tone_alert(
                frequencies=[262, 330],
                durations=[0.2, 0.2, 0.2]
            )


# ==================== PopupAlert 测试 ====================

class TestPopupAlert:
    """PopupAlert 类的测试套件"""

    def test_generate_message_good_status(self):
        """测试良好状态生成消息"""
        popup = PopupAlert()
        state = {'status': 'good', 'issues': []}

        message = popup.generate_message(state)

        assert message['severity'] == 'good'
        assert message['issues'] == []
        assert message['suggestions'] == []
        assert '良好' in message['summary']

    def test_generate_message_warning_single_issue(self):
        """测试警告状态单个问题"""
        popup = PopupAlert()
        state = {
            'status': 'warning',
            'issues': ['head_forward'],
            'angles': {'head_forward': 25.5}
        }

        message = popup.generate_message(state)

        assert message['title'] == '坐姿提醒'
        assert message['severity'] == 'warning'
        assert len(message['issues']) == 1
        assert message['issues'][0]['type'] == 'head_forward'
        assert '头部前倾' in message['issues'][0]['description']
        assert '25.5' in message['issues'][0]['description']
        assert len(message['suggestions']) > 0
        assert '头部前倾' in message['summary']

    def test_generate_message_bad_multiple_issues(self):
        """测试严重状态多个问题"""
        popup = PopupAlert()
        state = {
            'status': 'bad',
            'issues': ['head_forward', 'hunchback'],
            'angles': {'head_forward': 35.0, 'hunchback': 40.0}
        }

        message = popup.generate_message(state)

        assert message['title'] == '坐姿警告'
        assert message['severity'] == 'bad'
        assert len(message['issues']) == 2
        assert '严重' in message['summary']
        # 应包含两种问题的建议
        assert len(message['suggestions']) >= 2

    def test_generate_message_no_angles(self):
        """测试没有角度数据的情况"""
        popup = PopupAlert()
        state = {
            'status': 'warning',
            'issues': ['crossed_legs']
        }

        message = popup.generate_message(state)

        assert message['issues'][0]['type'] == 'crossed_legs'
        assert '跷二郎腿' in message['issues'][0]['description']
        # 不应包含角度数据
        assert '°' not in message['issues'][0]['description']

    def test_collect_suggestions_deduplication(self):
        """测试建议去重功能"""
        popup = PopupAlert()

        # 模拟重复的建议（虽然实际配置中可能不会重复）
        issues = ['head_forward', 'hunchback']
        suggestions = popup._collect_suggestions(issues)

        # 检查去重（每条建议只出现一次）
        assert len(suggestions) == len(set(suggestions))

    def test_format_suggestions(self):
        """测试格式化建议为字符串"""
        popup = PopupAlert()
        issues = ['head_forward']

        formatted = popup.format_suggestions(issues)

        assert '1.' in formatted
        assert '屏幕' in formatted or '头部' in formatted

    def test_format_suggestions_empty(self):
        """测试格式化空建议列表"""
        popup = PopupAlert()
        formatted = popup.format_suggestions([])

        assert '暂无' in formatted

    def test_create_custom_message(self):
        """测试创建自定义消息"""
        custom = PopupAlert.create_custom_message(
            title='自定义标题',
            severity='info',
            issues=[{'type': 'custom', 'description': '自定义问题'}],
            suggestions=['建议1', '建议2'],
            summary='自定义总结'
        )

        assert custom['title'] == '自定义标题'
        assert custom['severity'] == 'info'
        assert len(custom['issues']) == 1
        assert len(custom['suggestions']) == 2
        assert custom['summary'] == '自定义总结'

    def test_get_quick_message(self):
        """测试获取快速提示消息"""
        popup = PopupAlert()
        message = popup.get_quick_message('head_forward')

        assert '头部前倾' in message
        assert '建议' in message or '调整' in message

    def test_get_quick_message_unknown_issue(self):
        """测试获取未知问题的快速提示"""
        popup = PopupAlert()
        message = popup.get_quick_message('unknown_issue')

        assert 'unknown_issue' in message
        assert '注意调整' in message


# ==================== AlertConfig 测试 ====================

class TestAlertConfig:
    """AlertConfig 配置类的测试套件"""

    def test_get_cooldown_time(self):
        """测试获取冷却时间"""
        assert AlertConfig.get_cooldown_time('good') == float('inf')
        assert AlertConfig.get_cooldown_time('warning') == 60.0
        assert AlertConfig.get_cooldown_time('bad') == 30.0
        # 未知严重程度应返回默认值
        assert AlertConfig.get_cooldown_time('unknown') == AlertConfig.DEFAULT_COOLDOWN_SECONDS

    def test_get_status_color(self):
        """测试获取状态颜色"""
        assert AlertConfig.get_status_color('good') == 'green'
        assert AlertConfig.get_status_color('warning') == 'yellow'
        assert AlertConfig.get_status_color('bad') == 'red'
        assert AlertConfig.get_status_color('unknown') == 'gray'

    def test_get_status_label(self):
        """测试获取状态标签"""
        assert AlertConfig.get_status_label('good') == '坐姿良好'
        assert AlertConfig.get_status_label('warning') == '坐姿欠佳'
        assert AlertConfig.get_status_label('bad') == '坐姿不良'
        assert AlertConfig.get_status_label('unknown') == '未知状态'

    def test_get_sound_params(self):
        """测试获取音频参数"""
        warning_params = AlertConfig.get_sound_params('warning')
        assert warning_params['frequency'] == 440
        assert warning_params['wave_type'] == 'sine'

        bad_params = AlertConfig.get_sound_params('bad')
        assert bad_params['frequency'] == 880
        assert bad_params['wave_type'] == 'square'

    def test_get_issue_description(self):
        """测试获取问题描述"""
        assert AlertConfig.get_issue_description('head_forward') == '头部前倾'
        assert AlertConfig.get_issue_description('hunchback') == '驼背'
        assert AlertConfig.get_issue_description('crossed_legs') == '跷二郎腿'
        # 未知问题应返回原值
        assert AlertConfig.get_issue_description('unknown') == 'unknown'

    def test_get_issue_suggestions(self):
        """测试获取问题建议"""
        suggestions = AlertConfig.get_issue_suggestions('head_forward')
        assert len(suggestions) > 0
        assert any('屏幕' in s for s in suggestions)

        suggestions = AlertConfig.get_issue_suggestions('hunchback')
        assert len(suggestions) > 0
        assert any('背部' in s for s in suggestions)

        # 未知问题应返回空列表
        assert AlertConfig.get_issue_suggestions('unknown') == []


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试：测试各组件协同工作"""

    def test_full_alert_workflow(self):
        """测试完整的提醒工作流程"""
        manager = AlertManager()

        # 模拟检测到坐姿问题的过程
        posture_state = {
            'status': 'warning',
            'issues': ['head_forward'],
            'angles': {'head_forward': 30.0},
            'timestamp': time.time()
        }

        # 前两次不应触发提醒（未达阈值）
        for _ in range(AlertConfig.TRIGGER_THRESHOLD - 1):
            result = manager.check_and_alert(posture_state)
            assert result['should_alert'] is False

        # 第三次应触发提醒
        result = manager.check_and_alert(posture_state)
        assert result['should_alert'] is True

        # 验证声音提醒参数
        assert result['sound_alert']['frequency'] == 440
        assert result['sound_alert']['wave_type'] == 'sine'

        # 验证弹窗消息
        assert result['popup_alert']['severity'] == 'warning'
        assert '头部前倾' in result['popup_alert']['summary']
        assert len(result['popup_alert']['suggestions']) > 0

        # 验证状态指示
        assert result['status_indicator']['status'] == 'warning'
        assert result['status_indicator']['color'] == 'yellow'

    def test_alert_escalation(self):
        """测试提醒升级场景"""
        manager = AlertManager()

        # 先触发 warning 提醒
        warning_state = {
            'status': 'warning',
            'issues': ['head_forward']
        }
        for _ in range(AlertConfig.TRIGGER_THRESHOLD):
            manager.check_and_alert(warning_state)

        # 问题恶化为 bad
        bad_state = {
            'status': 'bad',
            'issues': ['head_forward', 'hunchback']
        }

        # 由于严重程度升级，冷却时间缩短，应该能更快触发
        with patch('time.time') as mock_time:
            mock_time.return_value = manager._last_alert_time + 20.0
            for _ in range(AlertConfig.TRIGGER_THRESHOLD):
                result = manager.check_and_alert(bad_state)

            # 验证触发了更严重的提醒
            assert result['should_alert'] is True
            assert result['sound_alert']['frequency'] == 880  # 更高频率
            assert result['popup_alert']['severity'] == 'bad'
