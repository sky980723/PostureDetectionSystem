#!/bin/bash
# 提醒系统测试运行脚本
#
# 用途: 运行提醒系统的所有单元测试并生成覆盖率报告
# 使用方法: bash run_alert_tests.sh

set -e  # 遇到错误立即退出

echo "========================================"
echo "  PostureDetectionSystem - 提醒系统测试"
echo "========================================"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境 .venv 不存在"
    echo "请先运行: python3 -m venv .venv"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 检查 pytest 是否安装
if ! python -c "import pytest" 2>/dev/null; then
    echo "错误: pytest 未安装"
    echo "请先运行: pip install -r requirements.txt"
    exit 1
fi

# 运行测试
echo ""
echo "运行测试..."
echo "----------------------------------------"
pytest tests/test_alerts.py \
    --cov=src/alerts \
    --cov=config/alert_config \
    --cov-report=term-missing \
    --cov-report=html \
    -v

# 检查测试结果
TEST_EXIT_CODE=$?

echo ""
echo "----------------------------------------"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ 所有测试通过！"
    echo ""
    echo "覆盖率报告已生成："
    echo "  - 终端报告: 见上方输出"
    echo "  - HTML 报告: htmlcov/index.html"
    echo ""
    echo "查看 HTML 报告: open htmlcov/index.html"
else
    echo "✗ 测试失败，请检查错误信息"
    exit $TEST_EXIT_CODE
fi
