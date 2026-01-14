#!/usr/bin/env python3
"""
测试纯 base64 数据发送
"""

import asyncio
import json
import websockets
import base64
from datetime import datetime
from PIL import Image
from io import BytesIO


async def test_pure_base64():
    """测试发送纯 base64（不带 data:image/ 前缀）"""
    uri = "ws://localhost:8000/ws/posture"

    print(f"🔗 连接到: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功！")

            # 创建一个简单的测试图片（640x480）
            img = Image.new('RGB', (640, 480), color='blue')
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            img_bytes = buffer.getvalue()
            base64_data = base64.b64encode(img_bytes).decode('utf-8')

            # 发送纯 base64（模拟前端）
            test_message = {
                "type": "video_frame",
                "data": base64_data,  # 纯 base64，无前缀
                "timestamp": datetime.now().timestamp()
            }

            print("\n📤 发送纯 base64 数据（无 data:image/ 前缀）...")
            print(f"   数据长度: {len(base64_data)} 字符")
            print(f"   前50字符: {base64_data[:50]}...")

            await websocket.send(json.dumps(test_message))

            # 等待响应
            print("⏳ 等待响应...")
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)

            response_data = json.loads(response)
            print("\n✅ 收到响应:")
            print(f"   类型: {response_data.get('type')}")
            print(f"   检测到人体: {response_data.get('detected')}")

            if response_data.get('type') == 'error':
                print(f"   ❌ 错误: {response_data.get('message')}")
                return False
            else:
                print("   ✅ 成功处理纯 base64 数据！")
                return True

    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("测试纯 base64 数据发送（修复验证）")
    print("=" * 60)
    print()

    success = await test_pure_base64()

    print()
    print("=" * 60)
    if success:
        print("✅ 测试通过 - 修复成功！")
    else:
        print("❌ 测试失败")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
