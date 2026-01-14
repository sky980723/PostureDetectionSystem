# 提醒系统使用示例

本文档展示如何使用提醒系统的各个组件。

## 目录结构

```
src/alerts/
├── __init__.py          # 模块导出
├── alert_manager.py     # 提醒管理器
├── sound_alert.py       # 声音提醒
└── popup_alert.py       # 弹窗提醒

config/
└── alert_config.py      # 配置文件

tests/
└── test_alerts.py       # 单元测试
```

## 基础使用

### 1. 创建提醒管理器

```python
from src.alerts import AlertManager

# 使用默认配置
manager = AlertManager()

# 自定义配置
manager = AlertManager(
    cooldown_seconds=60.0,  # 自定义冷却时间
    enable_sound=True,      # 启用声音提醒
    enable_popup=True       # 启用弹窗提醒
)
```

### 2. 检查姿态并触发提醒

```python
# 构建姿态状态数据
posture_state = {
    'status': 'warning',              # 状态: good/warning/bad
    'issues': ['head_forward'],       # 问题列表
    'angles': {'head_forward': 30.0}, # 角度数据（可选）
    'timestamp': time.time()          # 时间戳（可选）
}

# 检查并触发提醒
result = manager.check_and_alert(posture_state)

# 处理返回结果
if result['should_alert']:
    print("触发提醒！")

    # 获取声音提醒参数
    if result['sound_alert']:
        sound_params = result['sound_alert']
        # 在前端使用 Web Audio API 播放声音
        print(f"播放音频: {sound_params['frequency']} Hz")

    # 获取弹窗消息
    if result['popup_alert']:
        popup_data = result['popup_alert']
        print(f"标题: {popup_data['title']}")
        print(f"总结: {popup_data['summary']}")
        for suggestion in popup_data['suggestions']:
            print(f"  - {suggestion}")

# 获取状态指示
status_indicator = result['status_indicator']
print(f"状态: {status_indicator['label']} ({status_indicator['color']})")
```

### 3. 获取状态指示信息

```python
# 用于状态栏显示
indicator = manager.get_status_indicator('warning')
# 返回: {'status': 'warning', 'color': 'yellow', 'label': '坐姿欠佳'}
```

### 4. 重置管理器

```python
# 清除所有状态，重新开始监测
manager.reset()
```

### 5. 查询冷却时间

```python
# 获取距离下次提醒的剩余时间
remaining = manager.get_time_until_next_alert()
if remaining is None:
    print("可以立即提醒")
else:
    print(f"还需等待 {remaining:.1f} 秒")
```

## 声音提醒

### 1. 生成标准音频参数

```python
from src.alerts import SoundAlert

sound = SoundAlert()

# 警告级别音效
warning_params = sound.generate_alert_params('warning')
# 返回: {
#   'frequency': 440,
#   'duration': 0.3,
#   'volume': 0.5,
#   'wave_type': 'sine',
#   'pattern': [...]
# }

# 严重级别音效
bad_params = sound.generate_alert_params('bad')
# 返回更高频率、更长时长的参数
```

### 2. 创建自定义音效

```python
# 自定义单音调
custom_params = SoundAlert.create_custom_alert(
    frequency=500,      # Hz
    duration=0.4,       # 秒
    volume=0.6,         # 0-1
    wave_type='triangle'  # sine/square/triangle/sawtooth
)

# 自定义多音调（和弦或旋律）
multi_params = SoundAlert.create_multi_tone_alert(
    frequencies=[262, 330, 392],  # C, E, G 和弦
    durations=[0.2, 0.2, 0.2],
    volume=0.5,
    wave_type='sine'
)
```

### 3. 在前端播放音频

```javascript
// 前端 JavaScript 代码示例
function playAlert(soundParams) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const pattern = soundParams.pattern;
    let startTime = audioContext.currentTime;

    pattern.forEach(note => {
        if (note.frequency > 0) {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.type = soundParams.wave_type;
            oscillator.frequency.value = note.frequency;

            gainNode.gain.value = soundParams.volume;

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.start(startTime);
            oscillator.stop(startTime + note.duration);
        }
        startTime += note.duration;
    });
}
```

## 弹窗提醒

### 1. 生成弹窗消息

```python
from src.alerts import PopupAlert

popup = PopupAlert()

# 生成消息
message = popup.generate_message(posture_state)

# 消息结构
# {
#   'title': '坐姿提醒',
#   'severity': 'warning',
#   'issues': [
#       {'type': 'head_forward', 'description': '头部前倾（30.0°）'}
#   ],
#   'suggestions': ['调整屏幕高度...', '将头部向后收...'],
#   'summary': '检测到以下坐姿问题：头部前倾。请及时调整！'
# }
```

### 2. 格式化建议文本

```python
# 将建议列表格式化为带序号的文本
formatted = popup.format_suggestions(['head_forward', 'hunchback'])
print(formatted)
# 输出:
# 1. 调整屏幕高度，使视线平视
# 2. 将头部向后收，保持颈椎自然曲线
# 3. 避免长时间低头
# 4. 挺胸收腹，保持背部挺直
# ...
```

### 3. 快速提示消息

```python
# 获取简短的单行提示
quick_msg = popup.get_quick_message('head_forward')
print(quick_msg)
# 输出: "检测到头部前倾，建议：调整屏幕高度，使视线平视。"
```

### 4. 自定义消息

```python
# 完全自定义弹窗内容
custom_msg = PopupAlert.create_custom_message(
    title='自定义标题',
    severity='info',
    issues=[
        {'type': 'custom', 'description': '自定义问题描述'}
    ],
    suggestions=['建议1', '建议2'],
    summary='自定义总结文本'
)
```

## 完整工作流程示例

```python
import time
from src.alerts import AlertManager

def monitor_posture():
    """模拟持续监测坐姿的过程"""
    manager = AlertManager()

    while True:
        # 假设从检测引擎获取姿态数据
        posture_state = get_posture_from_detector()

        # 检查并触发提醒
        result = manager.check_and_alert(posture_state)

        # 更新 UI 状态指示
        update_status_bar(result['status_indicator'])

        # 如果需要提醒
        if result['should_alert']:
            # 播放声音
            if result['sound_alert']:
                play_sound_alert(result['sound_alert'])

            # 显示弹窗
            if result['popup_alert']:
                show_popup(result['popup_alert'])

        # 等待一段时间后继续检测
        time.sleep(1.0)

def get_posture_from_detector():
    """从姿态检测器获取数据（示例）"""
    # 实际使用时从 PostureAnalyzer 获取
    return {
        'status': 'warning',
        'issues': ['head_forward'],
        'angles': {'head_forward': 30.0},
        'timestamp': time.time()
    }

def update_status_bar(indicator):
    """更新状态栏（示例）"""
    print(f"状态栏: {indicator['label']} [{indicator['color']}]")

def play_sound_alert(sound_params):
    """播放声音提醒（示例）"""
    print(f"播放提醒音: {sound_params['frequency']} Hz")

def show_popup(popup_data):
    """显示弹窗（示例）"""
    print(f"弹窗标题: {popup_data['title']}")
    print(f"总结: {popup_data['summary']}")
    print("建议:")
    for i, suggestion in enumerate(popup_data['suggestions'], 1):
        print(f"  {i}. {suggestion}")

if __name__ == '__main__':
    monitor_posture()
```

## 配置自定义

如果需要修改默认配置，编辑 `config/alert_config.py`：

```python
# 修改冷却时间
AlertConfig.COOLDOWN_BY_SEVERITY['warning'] = 90.0  # 改为 90 秒

# 修改音频参数
AlertConfig.SOUND_PARAMS['warning']['frequency'] = 500  # 改为 500 Hz

# 修改提醒文案
AlertConfig.ISSUE_DESCRIPTIONS['head_forward'] = '头部过度前倾'

# 添加新的问题类型
AlertConfig.ISSUE_DESCRIPTIONS['slouching'] = '懈怠坐姿'
AlertConfig.ISSUE_SUGGESTIONS['slouching'] = [
    '坐直身体',
    '调整椅背角度'
]
```

## 测试

运行单元测试：

```bash
# 使用提供的脚本
bash run_alert_tests.sh

# 或直接使用 pytest
pytest tests/test_alerts.py --cov=src/alerts --cov-report=term-missing -v
```

测试覆盖了以下场景：
- 提醒触发逻辑（连续检测阈值）
- 冷却时间机制
- 状态升级处理
- 声音参数生成（包括自定义参数验证）
- 弹窗消息生成（包括多问题场景）
- 配置读取和边界情况

## 注意事项

1. **时间依赖**: AlertManager 使用 `time.time()` 管理冷却时间，测试时可使用 `unittest.mock.patch` 模拟时间
2. **线程安全**: 当前实现不是线程安全的，如需在多线程环境使用，请添加锁机制
3. **前端集成**: 音频播放需要在前端使用 Web Audio API 实现，本模块只提供参数
4. **扩展性**: 可以通过继承 AlertManager 添加自定义提醒类型（如邮件提醒、系统通知等）

## API 文档

详细的 API 文档请参考各类的 docstring：
- `AlertManager.check_and_alert()` - 主要入口方法
- `SoundAlert.generate_alert_params()` - 音频参数生成
- `PopupAlert.generate_message()` - 弹窗消息生成
- `AlertConfig` - 所有配置参数
