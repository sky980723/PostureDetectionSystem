#!/usr/bin/env python3
"""
WebSocket 连接测试脚本

测试 ws://localhost:8000/ws/posture 连接
"""

import asyncio
import json
import websockets
from datetime import datetime


async def test_websocket_connection():
    """测试 WebSocket 连接"""
    uri = "ws://localhost:8000/ws/posture"

    print(f"🔗 尝试连接到: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功！")

            # 发送一个测试消息
            test_message = {
                "type": "video_frame",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",  # 1x1 透明图片
                "timestamp": datetime.now().timestamp()
            }

            print("\n📤 发送测试帧...")
            await websocket.send(json.dumps(test_message))

            # 等待响应
            print("⏳ 等待响应...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)

            print("✅ 收到响应:")
            response_data = json.loads(response)
            print(json.dumps(response_data, indent=2, ensure_ascii=False))

            return True

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket 连接失败: HTTP {e.status_code}")
        print(f"   响应头: {e.headers}")
        return False

    except asyncio.TimeoutError:
        print("❌ 等待响应超时")
        return False

    except ConnectionRefusedError:
        print("❌ 连接被拒绝 - 服务器可能未运行")
        return False

    except Exception as e:
        print(f"❌ 连接错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("WebSocket 连接测试")
    print("=" * 60)
    print()

    success = await test_websocket_connection()

    print()
    print("=" * 60)
    if success:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
