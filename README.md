# 坐姿监测系统

基于 MediaPipe 的实时坐姿检测与提醒系统，包含后端 API、Web 前端、提醒策略与数据存储。适用于姿态监测、久坐提醒等场景。

## 功能特性

- 实时人体关键点检测与坐姿分析（头部前倾、驼背、跷二郎腿）
- WebSocket 视频流检测与 REST API
- 提醒系统（声音/弹窗/冷却时间）
- 记录存储与统计（SQLite + SQLAlchemy）
- 前端界面展示状态与历史统计

## 技术栈

- Python + FastAPI + WebSocket
- MediaPipe / OpenCV / NumPy
- SQLAlchemy 2.0 + aiosqlite
- Jinja2 模板与静态资源

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python run_server.py
```

或使用 uvicorn：

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问地址

- 主页面: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 配置

- 姿态检测配置：`config/settings.py`，环境变量前缀 `POSTURE_`
- API 配置：`config/api_settings.py`，环境变量前缀 `API_`
- 数据库默认位置：`data/posture.db`

示例：

```bash
export POSTURE_HEAD_FORWARD_ANGLE_THRESHOLD=20.0
export POSTURE_HUNCHBACK_OFFSET_THRESHOLD=0.15
export API_PORT=8080
```

## 目录结构

```text
PostureDetectionSystem/
├── src/
│   ├── api/          # FastAPI 后端
│   ├── web/          # 前端页面与静态资源
│   ├── detectors/    # 姿态检测
│   ├── analyzers/    # 姿态分析
│   ├── alerts/       # 提醒系统
│   ├── storage/      # 数据存储服务
│   └── models/       # 数据模型
├── config/           # 配置文件
├── tests/            # 单元测试
├── data/             # SQLite 数据库文件
└── docs/             # 文档
```

## 测试

```bash
pytest tests/ --cov=src -v
```

如需查看覆盖率报告：

```bash
pytest tests/ --cov=src --cov-report=html
```

## 相关文档

- `START.md`: 启动说明
- `USAGE.md`: 使用说明
- `TECHNICAL_DELIVERY.md`: 技术交付
- `PROJECT_STRUCTURE.md`: 项目结构与算法说明
- `STORAGE_README.md`: 存储层实现说明
