import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            print("成功连接到 WebSocket 服务器")
            
            # 发送测试消息（模拟弹幕事件）
            test_message = {
                "type": "input:text",
                "data": {
                    "text": "这是一条测试弹幕"
                }
            }
            await websocket.send(json.dumps(test_message))
            print("已发送测试弹幕消息")
            
            # 接收响应（可选）
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"收到响应: {response}")
            except asyncio.TimeoutError:
                print("等待响应超时")
                
    except Exception as e:
        print(f"连接失败: {e}")

# 运行测试
if __name__ == "__main__":
    asyncio.run(test_websocket())