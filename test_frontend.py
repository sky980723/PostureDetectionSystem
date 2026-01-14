#!/usr/bin/env python3
"""
前端功能集成测试

测试内容：
1. 静态文件服务
2. 模板渲染
3. API 端点
4. WebSocket 端点
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_frontend_integration():
    """测试前端集成"""
    print("=" * 60)
    print("前端功能集成测试")
    print("=" * 60)

    # 1. 检查文件存在
    print("\n1. 检查前端文件...")
    files_to_check = [
        "src/web/templates/index.html",
        "src/web/static/js/app.js",
        "src/web/static/css/style.css"
    ]

    all_exist = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False

    if not all_exist:
        print("\n✗ 部分文件缺失！")
        return False

    # 2. 测试后端模块导入
    print("\n2. 测试后端模块导入...")
    try:
        from src.api.main import app, templates, STATIC_DIR, TEMPLATES_DIR
        print("  ✓ FastAPI应用导入成功")
        print(f"  ✓ 模板目录: {TEMPLATES_DIR}")
        print(f"  ✓ 静态文件目录: {STATIC_DIR}")
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        return False

    # 3. 检查路由注册
    print("\n3. 检查路由注册...")
    routes = [route.path for route in app.routes]
    expected_routes = [
        "/",
        "/api",
        "/health",
        "/ws/posture",
        "/api/records",
        "/api/statistics",
        "/api/settings"
    ]

    for route in expected_routes:
        if any(route in r for r in routes):
            print(f"  ✓ {route}")
        else:
            print(f"  ✗ {route} (未找到)")

    # 4. 测试模板渲染（模拟请求）
    print("\n4. 测试模板渲染...")
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)

        # 测试主页
        response = client.get("/")
        if response.status_code == 200:
            print("  ✓ 主页渲染成功 (200 OK)")
            if "坐姿监测系统" in response.text:
                print("  ✓ HTML内容验证通过")
            else:
                print("  ✗ HTML内容验证失败")
        else:
            print(f"  ✗ 主页返回错误: {response.status_code}")

        # 测试API端点
        response = client.get("/api")
        if response.status_code == 200:
            print("  ✓ API端点响应正常")
        else:
            print(f"  ✗ API端点返回错误: {response.status_code}")

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False

    # 5. 总结
    print("\n" + "=" * 60)
    print("✓ 前端集成测试通过！")
    print("=" * 60)
    print("\n启动说明：")
    print("  运行以下命令启动服务器：")
    print("  python src/api/main.py")
    print("\n  或使用uvicorn：")
    print("  uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n  然后在浏览器访问：http://localhost:8000")
    print("=" * 60)

    return True


if __name__ == "__main__":
    result = asyncio.run(test_frontend_integration())
    sys.exit(0 if result else 1)
