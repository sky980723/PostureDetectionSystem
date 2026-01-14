"""
FastAPI 主应用单元测试

测试应用生命周期和全局异常处理
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient


# ============================================================================
# 测试用例：应用生命周期
# ============================================================================

@pytest.mark.asyncio
async def test_lifespan_startup():
    """测试应用启动时的初始化"""
    with patch('src.api.main.init_db') as mock_init_db:
        with patch('src.api.main.cleanup_detector') as mock_cleanup:
            with patch('src.api.main.close_db') as mock_close_db:
                # 导入 lifespan 函数
                from src.api.main import lifespan, app

                # 测试启动
                async with lifespan(app):
                    # 验证 init_db 被调用
                    mock_init_db.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_shutdown():
    """测试应用关闭时的资源清理"""
    with patch('src.api.main.init_db') as mock_init_db:
        with patch('src.api.main.cleanup_detector') as mock_cleanup:
            with patch('src.api.main.close_db') as mock_close_db:
                # 导入 lifespan 函数
                from src.api.main import lifespan, app

                # 测试完整的生命周期
                async with lifespan(app):
                    pass  # 进入上下文

                # 验证关闭时的清理操作
                mock_cleanup.assert_called_once()
                mock_close_db.assert_called_once()


# ============================================================================
# 测试用例：全局异常处理
# ============================================================================

def test_global_exception_handler_coverage():
    """测试全局异常处理器的覆盖（通过触发异常）"""
    from src.api.main import app, global_exception_handler
    from fastapi import Request
    from unittest.mock import AsyncMock
    import pytest

    # 创建模拟的请求对象
    mock_request = AsyncMock(spec=Request)

    # 测试异常处理
    test_exception = ValueError("Test exception")

    # 直接测试异常处理器函数
    import asyncio
    response = asyncio.run(global_exception_handler(mock_request, test_exception))

    # 验证返回 JSONResponse
    assert response.status_code == 500
    # 验证响应体包含错误信息
    import json
    body = json.loads(response.body.decode())
    assert "error" in body or "detail" in body


# ============================================================================
# 测试用例：路由注册
# ============================================================================

def test_routes_registered():
    """测试所有路由是否正确注册"""
    from src.api.main import app

    # 获取所有路由
    routes = [route.path for route in app.routes]

    # 验证关键路由存在
    assert "/" in routes
    assert "/health" in routes
    assert "/ws/posture" in routes
    assert "/api/records" in routes or any("/api/records" in r for r in routes)
    assert "/api/statistics" in routes or any("/api/statistics" in r for r in routes)
    assert "/api/settings" in routes or any("/api/settings" in r for r in routes)
