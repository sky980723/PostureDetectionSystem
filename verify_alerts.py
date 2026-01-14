"""
提醒系统手动验证脚本

用于快速验证提醒系统的各项功能是否正常工作。
运行方式: python verify_alerts.py
"""

import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.alerts import AlertManager, SoundAlert, PopupAlert
from config.alert_config import AlertConfig


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def verify_alert_manager():
    """验证 AlertManager 功能"""
    print_section("1. AlertManager 功能验证")

    manager = AlertManager()
    print("✓ AlertManager 初始化成功")

    # 测试良好状态
    good_state = {'status': 'good', 'issues': []}
    result = manager.check_and_alert(good_state)
    assert result['should_alert'] is False
    print("✓ 良好状态不触发提醒")

    # 测试警告状态（未达阈值）
    warning_state = {
        'status': 'warning',
        'issues': ['head_forward'],
        'angles': {'head_forward': 30.0}
    }

    for i in range(AlertConfig.TRIGGER_THRESHOLD - 1):
        result = manager.check_and_alert(warning_state)
        assert result['should_alert'] is False

    print(f"✓ 连续检测 {AlertConfig.TRIGGER_THRESHOLD - 1} 次未触发提醒")

    # 达到阈值
    result = manager.check_and_alert(warning_state)
    assert result['should_alert'] is True
    assert result['sound_alert'] is not None
    assert result['popup_alert'] is not None
    print(f"✓ 第 {AlertConfig.TRIGGER_THRESHOLD} 次检测触发提醒")

    # 验证状态指示
    indicator = result['status_indicator']
    assert indicator['status'] == 'warning'
    assert indicator['color'] == 'yellow'
    assert indicator['label'] == '坐姿欠佳'
    print("✓ 状态指示信息正确")

    # 测试冷却时间
    result = manager.check_and_alert(warning_state)
    assert result['should_alert'] is False
    print("✓ 冷却时间机制正常")

    # 测试重置
    manager.reset()
    assert manager._last_alert_time is None
    print("✓ 重置功能正常")

    print("\n[AlertManager] 所有测试通过！")


def verify_sound_alert():
    """验证 SoundAlert 功能"""
    print_section("2. SoundAlert 功能验证")

    sound = SoundAlert()
    print("✓ SoundAlert 初始化成功")

    # 测试警告音效
    warning_params = sound.generate_alert_params('warning')
    assert warning_params['frequency'] == 440
    assert warning_params['duration'] == 0.3
    assert warning_params['wave_type'] == 'sine'
    assert len(warning_params['pattern']) == 1
    print("✓ 警告音效参数正确")
    print(f"  频率: {warning_params['frequency']} Hz")
    print(f"  时长: {warning_params['duration']} 秒")

    # 测试严重音效
    bad_params = sound.generate_alert_params('bad')
    assert bad_params['frequency'] == 880
    assert bad_params['duration'] == 0.5
    assert bad_params['wave_type'] == 'square'
    assert len(bad_params['pattern']) == 3  # beep-pause-beep
    print("✓ 严重音效参数正确")
    print(f"  频率: {bad_params['frequency']} Hz")
    print(f"  时长: {bad_params['duration']} 秒")
    print(f"  模式: 双音节 ({len(bad_params['pattern'])} 段)")

    # 测试自定义音效
    try:
        custom_params = SoundAlert.create_custom_alert(
            frequency=500,
            duration=0.4,
            volume=0.6,
            wave_type='triangle'
        )
        assert custom_params['frequency'] == 500
        print("✓ 自定义音效创建成功")
    except Exception as e:
        print(f"✗ 自定义音效失败: {e}")
        raise

    # 测试多音调
    try:
        multi_params = SoundAlert.create_multi_tone_alert(
            frequencies=[262, 330, 392],
            durations=[0.2, 0.2, 0.2]
        )
        assert len(multi_params['pattern']) == 3
        print("✓ 多音调创建成功")
    except Exception as e:
        print(f"✗ 多音调创建失败: {e}")
        raise

    # 测试参数验证
    try:
        SoundAlert.create_custom_alert(frequency=25000, duration=0.5)
        print("✗ 参数验证失败：应该拒绝无效频率")
        raise AssertionError("参数验证未生效")
    except ValueError:
        print("✓ 参数验证正常（正确拒绝无效参数）")

    print("\n[SoundAlert] 所有测试通过！")


def verify_popup_alert():
    """验证 PopupAlert 功能"""
    print_section("3. PopupAlert 功能验证")

    popup = PopupAlert()
    print("✓ PopupAlert 初始化成功")

    # 测试良好状态
    good_state = {'status': 'good', 'issues': []}
    message = popup.generate_message(good_state)
    assert message['severity'] == 'good'
    assert len(message['issues']) == 0
    print("✓ 良好状态消息正确")

    # 测试单个问题
    single_issue_state = {
        'status': 'warning',
        'issues': ['head_forward'],
        'angles': {'head_forward': 30.5}
    }
    message = popup.generate_message(single_issue_state)
    assert message['title'] == '坐姿提醒'
    assert message['severity'] == 'warning'
    assert len(message['issues']) == 1
    assert message['issues'][0]['type'] == 'head_forward'
    assert '头部前倾' in message['issues'][0]['description']
    assert '30.5' in message['issues'][0]['description']
    assert len(message['suggestions']) > 0
    print("✓ 单个问题消息正确")
    print(f"  标题: {message['title']}")
    print(f"  总结: {message['summary']}")
    print(f"  建议数量: {len(message['suggestions'])}")

    # 测试多个问题
    multi_issue_state = {
        'status': 'bad',
        'issues': ['head_forward', 'hunchback'],
        'angles': {'head_forward': 35.0, 'hunchback': 40.0}
    }
    message = popup.generate_message(multi_issue_state)
    assert message['title'] == '坐姿警告'
    assert message['severity'] == 'bad'
    assert len(message['issues']) == 2
    assert '严重' in message['summary']
    print("✓ 多个问题消息正确")
    print(f"  问题数量: {len(message['issues'])}")
    print(f"  建议数量: {len(message['suggestions'])}")

    # 测试格式化建议
    formatted = popup.format_suggestions(['head_forward'])
    assert '1.' in formatted
    print("✓ 建议格式化正常")
    print("  示例:")
    for line in formatted.split('\n')[:2]:
        print(f"    {line}")

    # 测试快速消息
    quick_msg = popup.get_quick_message('head_forward')
    assert '头部前倾' in quick_msg
    print("✓ 快速消息正常")
    print(f"  内容: {quick_msg}")

    print("\n[PopupAlert] 所有测试通过！")


def verify_config():
    """验证配置模块"""
    print_section("4. AlertConfig 配置验证")

    # 测试冷却时间
    assert AlertConfig.get_cooldown_time('good') == float('inf')
    assert AlertConfig.get_cooldown_time('warning') == 60.0
    assert AlertConfig.get_cooldown_time('bad') == 30.0
    print("✓ 冷却时间配置正确")

    # 测试状态颜色
    assert AlertConfig.get_status_color('good') == 'green'
    assert AlertConfig.get_status_color('warning') == 'yellow'
    assert AlertConfig.get_status_color('bad') == 'red'
    print("✓ 状态颜色配置正确")

    # 测试状态标签
    assert AlertConfig.get_status_label('good') == '坐姿良好'
    assert AlertConfig.get_status_label('warning') == '坐姿欠佳'
    assert AlertConfig.get_status_label('bad') == '坐姿不良'
    print("✓ 状态标签配置正确")

    # 测试问题描述
    assert AlertConfig.get_issue_description('head_forward') == '头部前倾'
    assert AlertConfig.get_issue_description('hunchback') == '驼背'
    assert AlertConfig.get_issue_description('crossed_legs') == '跷二郎腿'
    print("✓ 问题描述配置正确")

    # 测试问题建议
    suggestions = AlertConfig.get_issue_suggestions('head_forward')
    assert len(suggestions) > 0
    print(f"✓ 问题建议配置正确（头部前倾有 {len(suggestions)} 条建议）")

    print("\n[AlertConfig] 所有测试通过！")


def verify_integration():
    """验证完整工作流程"""
    print_section("5. 完整工作流程验证")

    manager = AlertManager()

    # 模拟完整的检测周期
    print("模拟连续检测...")

    posture_state = {
        'status': 'warning',
        'issues': ['head_forward'],
        'angles': {'head_forward': 30.0},
        'timestamp': time.time()
    }

    # 前几次不触发
    for i in range(AlertConfig.TRIGGER_THRESHOLD - 1):
        result = manager.check_and_alert(posture_state)
        print(f"  第 {i+1} 次检测: 未触发提醒")

    # 达到阈值触发
    result = manager.check_and_alert(posture_state)
    print(f"  第 {AlertConfig.TRIGGER_THRESHOLD} 次检测: 触发提醒！")

    # 验证所有组件都正常工作
    assert result['should_alert'] is True
    assert result['sound_alert'] is not None
    assert result['popup_alert'] is not None
    assert result['status_indicator'] is not None

    print("\n提醒详情:")
    print(f"  声音频率: {result['sound_alert']['frequency']} Hz")
    print(f"  弹窗标题: {result['popup_alert']['title']}")
    print(f"  状态指示: {result['status_indicator']['label']}")
    print(f"  建议数量: {len(result['popup_alert']['suggestions'])}")

    # 测试冷却后再次提醒
    print("\n测试冷却机制...")
    result = manager.check_and_alert(posture_state)
    assert result['should_alert'] is False
    print("  ✓ 冷却时间内阻止了重复提醒")

    remaining = manager.get_time_until_next_alert()
    print(f"  距离下次提醒还需: {remaining:.1f} 秒")

    print("\n[完整工作流程] 验证通过！")


def main():
    """主函数"""
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "PostureDetectionSystem - 提醒系统验证" + " " * 9 + "║")
    print("╚" + "═" * 58 + "╝")

    try:
        verify_alert_manager()
        verify_sound_alert()
        verify_popup_alert()
        verify_config()
        verify_integration()

        print_section("验证结果")
        print("✓✓✓ 所有功能验证通过！✓✓✓")
        print("\n提醒系统工作正常，可以继续进行集成测试。")
        print("\n下一步:")
        print("  1. 运行单元测试: bash run_alert_tests.sh")
        print("  2. 查看使用文档: docs/alert_system_usage.md")
        print("  3. 集成到 Web 服务: src/api/main.py")

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗✗✗ 验证失败 ✗✗✗")
        print("=" * 60)
        print(f"\n错误信息: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
