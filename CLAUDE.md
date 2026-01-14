# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PostureDetectionSystem 是一个基于Python的姿态检测系统项目。

## 开发环境

- **Python版本**: 3.13.3
- **虚拟环境**: 项目使用 `.venv` 目录管理虚拟环境
- **激活虚拟环境**:
  ```bash
  source .venv/bin/activate  # macOS/Linux
  ```

## 常用命令

### 依赖管理
```bash
# 安装依赖（当 requirements.txt 创建后）
pip install -r requirements.txt

# 导出依赖
pip freeze > requirements.txt
```

### 运行测试（待项目结构建立后）
```bash
# 运行所有测试
python -m pytest

# 运行单个测试文件
python -m pytest tests/test_specific.py

# 运行带覆盖率的测试
python -m pytest --cov=src tests/
```

### 代码质量检查（待工具配置后）
```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/
pylint src/

# 类型检查
mypy src/
```

## 预期架构（待开发）

典型的姿态检测系统通常包含以下模块：

- **数据采集模块**: 从摄像头或视频文件获取图像数据
- **预处理模块**: 图像预处理、增强、归一化
- **检测模块**: 使用深度学习模型（如MediaPipe、OpenPose等）进行人体关键点检测
- **分析模块**: 基于关键点数据分析姿态特征
- **可视化模块**: 结果展示和可视化
- **配置管理**: 系统参数配置

## 开发注意事项

- 项目当前为空白状态，尚未建立代码结构
- 开发时应遵循Python PEP 8编码规范
- 建议的目录结构：
  ```
  PostureDetectionSystem/
  ├── src/           # 源代码
  ├── tests/         # 测试代码
  ├── data/          # 数据文件
  ├── models/        # 训练模型
  ├── config/        # 配置文件
  └── docs/          # 文档
  ```