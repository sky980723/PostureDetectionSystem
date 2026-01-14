#!/bin/bash

# 激活虚拟环境并运行测试

set -e

echo "==================================="
echo "运行数据存储层单元测试"
echo "==================================="

# 激活虚拟环境
source .venv/bin/activate

# 运行测试并生成覆盖率报告
pytest tests/test_storage.py \
  --cov=src/models \
  --cov=src/storage \
  --cov-report=term-missing \
  --cov-report=html \
  -v

echo ""
echo "==================================="
echo "测试完成！"
echo "HTML 覆盖率报告已生成到: htmlcov/index.html"
echo "==================================="
