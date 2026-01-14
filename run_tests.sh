#!/bin/bash
# 测试运行脚本

cd /Users/sky/python_demo/PostureDetectionSystem

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -q -r requirements.txt

# 运行测试
echo "================================"
echo "运行核心检测引擎测试"
echo "================================"

python -m pytest tests/test_detectors.py tests/test_analyzers.py \
    --cov=src/detectors \
    --cov=src/analyzers \
    --cov-report=term-missing \
    --cov-report=html \
    -v

echo ""
echo "================================"
echo "测试完成!"
echo "HTML 覆盖率报告: htmlcov/index.html"
echo "================================"
