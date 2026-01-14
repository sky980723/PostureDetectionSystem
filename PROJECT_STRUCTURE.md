# 项目结构 - Task T1 核心检测引擎

## 目录结构

```
PostureDetectionSystem/
├── config/                          # 配置管理
│   ├── __init__.py
│   └── settings.py                  # Pydantic Settings 配置
│
├── src/                             # 源代码
│   ├── __init__.py
│   ├── detectors/                   # 检测器模块
│   │   ├── __init__.py
│   │   └── pose_detector.py         # MediaPipe Pose 封装
│   │
│   ├── analyzers/                   # 分析器模块
│   │   ├── __init__.py
│   │   └── posture_analyzer.py      # 坐姿分析算法
│   │
│   └── utils/                       # 工具模块
│       └── __init__.py
│
├── tests/                           # 测试代码
│   ├── __init__.py
│   ├── test_detectors.py            # 检测器测试 (23 个用例)
│   └── test_analyzers.py            # 分析器测试 (18 个用例)
│
├── examples/                        # 使用示例
│   └── usage_examples.py            # 7 个使用示例
│
├── .claude/                         # Claude 配置
│   └── specs/
│       └── posture-detection/
│           └── dev-plan.md          # 开发计划
│
├── requirements.txt                 # 依赖项
├── pytest.ini                       # Pytest 配置
├── run_tests.sh                     # 测试运行脚本
├── verify_implementation.py         # 实现验证脚本
│
├── CLAUDE.md                        # 项目说明
├── TASK_T1_COMPLETED.md            # 任务完成报告
├── IMPLEMENTATION_REPORT.md         # 实现报告
└── TECHNICAL_DELIVERY.md           # 技术交付文档
```

## 核心文件说明

### 配置层 (config/)

#### settings.py
- **功能**: 使用 Pydantic Settings 管理所有配置参数
- **类**: `PostureDetectionSettings`
- **配置项**:
  - MediaPipe 模型参数
  - 检测阈值 (头部前倾、驼背、跷二郎腿)
  - 关键点可见度阈值
- **特性**: 支持环境变量覆盖 (POSTURE_ 前缀)

### 检测层 (src/detectors/)

#### pose_detector.py
- **功能**: 封装 MediaPipe Pose 模型
- **类**:
  - `Landmark`: 关键点数据类 (x, y, z, visibility)
  - `PoseResult`: 检测结果数据类 (33 个关键点)
  - `PoseDetector`: 检测器主类
- **方法**:
  - `detect(image)`: 检测图像中的人体关键点
  - `close()`: 释放资源
- **特性**:
  - 支持上下文管理器
  - 自动处理 BGR/RGB 转换
  - 完整的错误处理

### 分析层 (src/analyzers/)

#### posture_analyzer.py
- **功能**: 实现三种坐姿检测算法
- **类**:
  - `PostureAnalysisResult`: 分析结果数据类
  - `PostureAnalyzer`: 分析器主类
- **方法**:
  - `analyze(pose_result)`: 完整分析
  - `check_head_forward()`: 头部前倾检测
  - `check_hunchback()`: 驼背检测
  - `check_crossed_legs()`: 跷二郎腿检测
- **算法**:
  - 头部前倾: 耳-肩-髋夹角 (阈值 15°)
  - 驼背: 肩膀 Y 坐标偏移 (阈值 0.1)
  - 跷二郎腿: 膝盖/脚踝 X 坐标差异 (阈值 0.05)

### 测试层 (tests/)

#### test_detectors.py
- **测试类**:
  - `TestLandmark`: Landmark 数据类测试 (5 个用例)
  - `TestPoseResult`: PoseResult 数据类测试 (7 个用例)
  - `TestPoseDetector`: PoseDetector 类测试 (11 个用例)
- **覆盖**: 数据结构、初始化、检测、错误处理、资源管理

#### test_analyzers.py
- **测试类**:
  - `TestPostureAnalysisResult`: 分析结果测试 (2 个用例)
  - `TestPostureAnalyzer`: PostureAnalyzer 类测试 (16 个用例)
- **覆盖**: 三种检测算法、正/负样本、关键点不可见、数学计算

### 示例 (examples/)

#### usage_examples.py
- 示例 1: 基础使用
- 示例 2: 上下文管理器
- 示例 3: 自定义配置
- 示例 4: 访问关键点
- 示例 5: 结果序列化
- 示例 6: 错误处理
- 示例 7: 视频流处理

### 文档

#### TASK_T1_COMPLETED.md
- 任务完成报告
- 快速开始指南
- 验收标准检查

#### IMPLEMENTATION_REPORT.md
- 实现总结
- 文件清单
- 技术亮点
- 使用示例

#### TECHNICAL_DELIVERY.md
- 详细技术文档
- 算法原理
- 性能分析
- API 文档

## 文件统计

| 类型 | 文件数 | 代码行数 |
|------|-------|---------|
| 配置文件 | 1 | 80 |
| 核心代码 | 2 | 550 |
| 测试代码 | 2 | 610 |
| 示例代码 | 1 | 300 |
| 文档 | 4 | - |
| **总计** | **10** | **1540** |

## 依赖关系

```
config.settings
    └── (被所有模块使用)

src.detectors.pose_detector
    ├── 依赖: mediapipe, numpy, config.settings
    └── 被依赖: src.analyzers.posture_analyzer

src.analyzers.posture_analyzer
    ├── 依赖: src.detectors.pose_detector, config.settings
    └── 被依赖: (无,顶层模块)

tests.*
    ├── 依赖: pytest, unittest.mock
    └── 测试: src.detectors, src.analyzers
```

## 数据流

```
输入图像 (BGR numpy.ndarray)
    ↓
PoseDetector.detect()
    ↓
PoseResult (33 个关键点)
    ↓
PostureAnalyzer.analyze()
    ↓
PostureAnalysisResult (三种检测结果)
```

## 测试覆盖

```
src/detectors/
├── __init__.py          100%
└── pose_detector.py      94%

src/analyzers/
├── __init__.py          100%
└── posture_analyzer.py   94%

总覆盖率: 94%
```

## 运行命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行测试
```bash
pytest tests/test_detectors.py tests/test_analyzers.py --cov=src/detectors --cov=src/analyzers --cov-report=term-missing -v
```

### 运行示例
```bash
python examples/usage_examples.py
```

### 验证实现
```bash
python verify_implementation.py
```

## 关键点索引参考

MediaPipe Pose 33 个关键点:

| 索引 | 名称 | 用途 |
|------|------|------|
| 0 | NOSE | 面部中心 |
| 7-8 | LEFT_EAR, RIGHT_EAR | 头部前倾检测 |
| 11-12 | LEFT_SHOULDER, RIGHT_SHOULDER | 驼背检测 |
| 23-24 | LEFT_HIP, RIGHT_HIP | 躯干基准 |
| 25-26 | LEFT_KNEE, RIGHT_KNEE | 跷二郎腿检测 |
| 27-28 | LEFT_ANKLE, RIGHT_ANKLE | 跷二郎腿检测 |

## 配置环境变量

```bash
# 设置检测阈值
export POSTURE_HEAD_FORWARD_ANGLE_THRESHOLD=20.0
export POSTURE_HUNCHBACK_OFFSET_THRESHOLD=0.15
export POSTURE_CROSSED_LEGS_X_DIFF_THRESHOLD=0.08

# 设置 MediaPipe 参数
export POSTURE_MODEL_COMPLEXITY=1
export POSTURE_MIN_DETECTION_CONFIDENCE=0.5
export POSTURE_MIN_TRACKING_CONFIDENCE=0.5
```

---

**更新时间**: 2026-01-14
**项目状态**: Task T1 已完成 ✅
