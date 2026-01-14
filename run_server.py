#!/usr/bin/env python3
"""
坐姿监测系统 - 服务器启动脚本

使用方法：
    python run_server.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """启动服务器"""
    import uvicorn
    from config.api_settings import api_settings

    print("=" * 60)
    print("🪑 坐姿监测系统")
    print("=" * 60)
    print(f"启动地址: http://{api_settings.host}:{api_settings.port}")
    print(f"API 文档: http://{api_settings.host}:{api_settings.port}/docs")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器\n")

    try:
        # 导入app（触发数据库初始化等）
        from src.api.main import app

        # 启动服务器
        uvicorn.run(
            app,
            host=api_settings.host,
            port=api_settings.port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
