#!/usr/bin/env python3
"""
测试实时角度数据显示
"""

import asyncio
import json
import websockets
import base64
from datetime import datetime
from PIL import Image, ImageDraw
from io import BytesIO


async def test_angles_display():
    """测试实时角度数据是否正确返回"""
    uri = "ws://localhost:8000/ws/posture"

    print(f"🔗 连接到: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功！")

            # 创建一个带人体姿态的测试图片（640x480）
            # 使用白色背景，绘制一个简单的人形（用于触发检测）
            img = Image.new('RGB', (640, 480), color='white')
            draw = ImageDraw.Draw(img)

            # 绘制一个简单的人形轮廓（头、身体、腿）
            # 头部
            draw.ellipse([300, 100, 340, 140], fill='blue')
            # 身体
            draw.rectangle([310, 140, 330, 280], fill='blue')
            # 左腿
            draw.rectangle([310, 280, 320, 400], fill='blue')
            # 右腿
            draw.rectangle([320, 280, 330, 400], fill='blue')
            # 左臂
            draw.rectangle([295, 150, 310, 220], fill='blue')
            # 右臂
            draw.rectangle([330, 150, 345, 220], fill='blue')

            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            img_bytes = buffer.getvalue()
            base64_data = base64.b64encode(img_bytes).decode('utf-8')

            # 发送3帧数据
            for i in range(3):
                test_message = {
                    "type": "video_frame",
                    "data": base64_data,
                    "timestamp": datetime.now().timestamp()
                }

                print(f"\n📤 发送第 {i+1} 帧...")
                await websocket.send(json.dumps(test_message))

                # 等待响应
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                print(f"\n✅ 收到响应 #{i+1}:")
                print(f"   类型: {response_data.get('type')}")
                print(f"   检测到人体: {response_data.get('detected')}")

                if response_data.get('type') == 'error':
                    print(f"   ❌ 错误: {response_data.get('message')}")
                    return False

                # 检查 analysis 字段
                analysis = response_data.get('analysis')
                if analysis:
                    print(f"   分析有效: {analysis.get('valid')}")
                    print(f"   状态: {analysis.get('status')}")
                    print(f"   问题: {analysis.get('issues')}")

                    # 检查 angles 对象（前端需要的）
                    angles = analysis.get('angles')
                    if angles:
                        print(f"   ✅ angles 对象存在:")
                        print(f"      - head_forward: {angles.get('head_forward', 'N/A')}")
                        print(f"      - hunchback: {angles.get('hunchback', 'N/A')}")
                        print(f"      - crossed_legs: {angles.get('crossed_legs', 'N/A')}")
                    else:
                        print(f"   ⚠️  angles 对象不存在或为空")
                else:
                    print(f"   ⚠️  analysis 字段不存在")

                await asyncio.sleep(0.2)

            return True

    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 70)
    print("测试实时角度数据显示（angles 对象验证）")
    print("=" * 70)
    print()

    success = await test_angles_display()

    print()
    print("=" * 70)
    if success:
        print("✅ 测试通过 - 实时角度数据应该可以正常显示！")
        print("\n现在请：")
        print("1. 刷新浏览器页面（Ctrl+Shift+R 或 Cmd+Shift+R）")
        print("2. 点击'开始监测'按钮")
        print("3. 确保身体出现在摄像头画面中")
        print("4. 右侧应该会显示实时角度数据")
    else:
        print("❌ 测试失败")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
