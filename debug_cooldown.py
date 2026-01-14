#!/usr/bin/env python3
"""调试冷却时间测试"""

import time
from unittest.mock import patch
from src.alerts.alert_manager import AlertManager, AlertConfig

def test_cooldown():
    manager = AlertManager(cooldown_seconds=5.0)
    posture_state = {
        'status': 'warning',
        'issues': ['head_forward'],
        'timestamp': time.time()
    }

    print(f"TRIGGER_THRESHOLD: {AlertConfig.TRIGGER_THRESHOLD}")

    # 先触发一次提醒
    print("\n=== 第一轮：达到触发阈值 ===")
    for i in range(AlertConfig.TRIGGER_THRESHOLD):
        result = manager.check_and_alert(posture_state)
        print(f"第{i+1}次: consecutive_count={manager._consecutive_issues_count}, should_alert={result['should_alert']}")

    print(f"\n触发后: _last_alert_time={manager._last_alert_time}")

    # 立即再次检查
    print("\n=== 第二轮：冷却期内 ===")
    result = manager.check_and_alert(posture_state)
    print(f"冷却期内: consecutive_count={manager._consecutive_issues_count}, should_alert={result['should_alert']}")

    # 手动修改_last_alert_time
    print("\n=== 第三轮：手动修改_last_alert_time ===")
    old_last_alert = manager._last_alert_time
    manager._last_alert_time = time.time() - 6.0
    print(f"修改前: {old_last_alert}")
    print(f"修改后: {manager._last_alert_time}")
    print(f"当前时间: {time.time()}")
    print(f"时间差: {time.time() - manager._last_alert_time}秒")
    result = manager.check_and_alert(posture_state)
    print(f"冷却期后: consecutive_count={manager._consecutive_issues_count}, should_alert={result['should_alert']}")

if __name__ == '__main__':
    test_cooldown()
