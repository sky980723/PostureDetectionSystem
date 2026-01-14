# 坐姿监测系统 - 使用说明

## 🎉 系统已完成

所有功能已开发完成并通过测试！

- ✅ **核心检测引擎** (100%覆盖率)
- ✅ **数据存储层** (100%覆盖率)
- ✅ **提醒系统** (100%覆盖率)
- ✅ **Web服务后端** (98%覆盖率)
- ✅ **前端界面** (全新实现)

**总测试覆盖率：99%** (165个测试全部通过)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

**方法1：直接运行**
```bash
python src/api/main.py
```

**方法2：使用uvicorn**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问系统

打开浏览器访问：**http://localhost:8000**

---

## 📖 功能说明

### 主界面布局

```
┌─────────────────────────────────────────────────┐
│  🪑 坐姿监测系统          ● 已连接     ⚙️      │
├──────────────────────┬──────────────────────────┤
│                      │  实时角度                │
│   视频画面            │  - 头部前倾: 12.5°      │
│   (带关键点标注)      │  - 驼背偏移: 0.08       │
│                      │  - 腿部差异: 0.03       │
│  [开始监测] [停止]    │                         │
│                      │  今日统计                │
│  FPS: 10             │  - 提醒次数: 3          │
│  检测状态: 检测中     │  - 监测时长: 45分钟     │
│  问题: 无             │  - 良好时长: 38分钟     │
│                      │                         │
│                      │  历史记录图表            │
│                      │  [柱状图显示]            │
└──────────────────────┴──────────────────────────┘
```

### 核心功能

#### 1. 实时姿态检测
- 使用MediaPipe检测33个人体关键点
- 实时分析坐姿状态（良好/欠佳/不良）
- Canvas绘制骨架和关键点标注

#### 2. 不良坐姿识别
- **头部前倾检测**：计算头部相对身体的角度
- **驼背检测**：分析肩膀和髋部的距离比例
- **跷二郎腿检测**：检测左右腿位置差异

#### 3. 多种提醒方式
- **声音提醒**：可自定义频率和音量
- **弹窗提醒**：显示具体问题和改进建议
- **状态指示器**：实时显示坐姿状态（绿/黄/红）

#### 4. 数据记录与统计
- 自动记录所有不良坐姿事件
- 支持按日/周/月查询历史数据
- 提供统计汇总和图表展示

---

## ⚙️ 系统设置

点击右上角 **⚙️** 按钮打开设置面板：

### 检测阈值
| 参数 | 默认值 | 说明 |
|------|--------|------|
| 头部前倾角度 | 15° | 低于此角度视为正常 |
| 驼背偏移阈值 | 0.1 | 肩膀髋部距离比例 |
| 跷腿差异阈值 | 0.05 | 左右腿位置差异 |

### 提醒设置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| 冷却时间 | 30秒 | 两次提醒的最小间隔 |
| 启用声音提醒 | ✓ | 播放提醒音 |
| 启用弹窗提醒 | ✓ | 显示提醒弹窗 |

---

## 🔌 API 端点

### REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/records` | GET | 获取历史记录 |
| `/api/statistics` | GET | 获取统计数据 |
| `/api/settings` | GET/PUT | 获取/更新设置 |
| `/health` | GET | 健康检查 |

### WebSocket

| 端点 | 说明 |
|------|------|
| `/ws/posture` | 实时姿态检测流 |

**发送格式：**
```json
{
  "type": "video_frame",
  "data": "base64_encoded_image",
  "timestamp": 1234567890.123
}
```

**接收格式：**
```json
{
  "type": "posture_result",
  "pose_landmarks": [...],
  "analysis": {
    "status": "warning",
    "issues": ["head_forward"],
    "angles": {...}
  },
  "alert": {
    "should_alert": true,
    "sound_alert": {...},
    "popup_alert": {...}
  }
}
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ --cov=src -v

# 运行特定模块测试
pytest tests/test_alerts.py -v
pytest tests/test_analyzers.py -v
pytest tests/test_detectors.py -v
pytest tests/test_storage.py -v
pytest tests/test_api*.py -v

# 查看覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

---

## 📁 项目结构

```
PostureDetectionSystem/
├── src/
│   ├── api/              # FastAPI 后端
│   │   ├── main.py       # 主应用
│   │   ├── routes/       # REST API 路由
│   │   ├── websocket/    # WebSocket 处理
│   │   └── schemas/      # 数据模型
│   ├── web/              # 前端
│   │   ├── templates/    # HTML 模板
│   │   └── static/       # 静态资源
│   │       ├── js/       # JavaScript
│   │       └── css/      # 样式表
│   ├── detectors/        # 姿态检测
│   ├── analyzers/        # 姿态分析
│   ├── alerts/           # 提醒系统
│   ├── storage/          # 数据存储
│   └── models/           # 数据库模型
├── tests/                # 单元测试
├── config/               # 配置文件
└── docs/                 # 文档
```

---

## 🔧 故障排除

### 1. 摄像头无法访问

**问题：** 浏览器提示"摄像头权限被拒绝"

**解决方案：**
- 检查浏览器设置，允许网站访问摄像头
- 确保使用HTTPS或localhost访问（WebRTC要求）
- 尝试其他浏览器（推荐Chrome/Edge）

### 2. WebSocket连接失败

**问题：** 控制台显示"WebSocket connection failed"

**解决方案：**
- 检查服务器是否正在运行
- 确认端口8000未被占用
- 检查防火墙设置

### 3. 检测不准确

**问题：** 姿态检测结果不稳定

**解决方案：**
- 确保光线充足
- 保持身体完整出现在画面中
- 调整摄像头角度，避免逆光
- 在设置中调整检测阈值

---

## 📝 开发日志

### 已完成功能

- [x] MediaPipe姿态检测封装
- [x] 坐姿分析算法实现
- [x] SQLite数据存储
- [x] 提醒系统（声音+弹窗）
- [x] FastAPI后端服务
- [x] WebSocket实时通信
- [x] 响应式前端界面
- [x] 历史数据查询和统计
- [x] 系统设置管理
- [x] 单元测试（165个，99%覆盖率）

### 技术栈

| 组件 | 技术 |
|------|------|
| 检测模型 | MediaPipe Pose |
| 后端框架 | FastAPI |
| 数据库 | SQLite + SQLAlchemy |
| 前端 | HTML5 + CSS3 + Vanilla JS |
| 通信 | WebSocket |
| 测试 | pytest + pytest-cov |

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🙏 致谢

- **MediaPipe** - Google的开源人体姿态检测库
- **FastAPI** - 现代高性能的Python Web框架
- **SQLAlchemy** - 强大的Python ORM库

---

**祝您使用愉快！保持良好坐姿，远离颈椎病！** 🪑✨
