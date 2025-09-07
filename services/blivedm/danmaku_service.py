# -*- coding: utf-8 -*-
import asyncio
import json
import os
from flask import Flask, jsonify
from flask_cors import CORS
import blivedm
import blivedm.models.open_live as open_models
import blivedm.models.web as web_models
import threading

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

# 从环境变量获取配置
ACCESS_KEY_ID = os.environ.get('ACCESS_KEY_ID')
ACCESS_KEY_SECRET = os.environ.get('ACCESS_KEY_SECRET')
APP_ID = os.environ.get('APP_ID')
ROOM_OWNER_AUTH_CODE = os.environ.get('ROOM_OWNER_AUTH_CODE')



# 全局变量存储客户端和处理器
client = None
handler = None

# 存储最新的弹幕消息
danmaku_messages = []

class DanmakuHandler(blivedm.BaseHandler):
    def __init__(self, emit_callback):
        self.emit_callback = emit_callback

    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    def _on_open_live_danmaku(self, client: blivedm.OpenLiveClient, message: open_models.DanmakuMessage):
        danmaku_data = {
            'type': 'danmaku',
            'uname': message.uname,
            'msg': message.msg,
            'uid': message.open_id,
            'room_id': message.room_id,
            'timestamp': message.timestamp,
        }
        self.emit_callback(danmaku_data)
        print(f"Received danmaku: {message.uname} - {message.msg}")

    def _on_open_live_gift(self, client: blivedm.OpenLiveClient, message: open_models.GiftMessage):
        gift_data = {
            'type': 'gift',
            'uname': message.uname,
            'uid': message.uid,
            'room_id': message.room_id,
            'gift_name': message.gift_name,
            'gift_num': message.gift_num,
            'price': message.price,
            'paid': message.paid,
            'timestamp': message.timestamp,
        }
        self.emit_callback(gift_data)

    def _on_open_live_buy_guard(self, client: blivedm.OpenLiveClient, message: open_models.GuardBuyMessage):
        guard_data = {
            'type': 'guard',
            'uname': message.user_info.uname,
            'uid': message.user_info.uid,
            'room_id': message.room_id,
            'guard_level': message.guard_level,
            'guard_name': message.guard_name,
            'price': message.price,
            'timestamp': message.timestamp,
        }
        self.emit_callback(guard_data)

    def _on_open_live_super_chat(self, client: blivedm.OpenLiveClient, message: open_models.SuperChatMessage):
        sc_data = {
            'type': 'superchat',
            'uname': message.uname,
            'uid': message.uid,
            'room_id': message.room_id,
            'message': message.message,
            'rmb': message.rmb,
            'timestamp': message.timestamp,
        }
        self.emit_callback(sc_data)

    def _on_open_live_like(self, client: blivedm.OpenLiveClient, message: open_models.LikeMessage):
        like_data = {
            'type': 'like',
            'uname': message.uname,
            'uid': message.uid,
            'room_id': message.room_id,
            'timestamp': message.timestamp,
        }
        self.emit_callback(like_data)

def emit_danmaku(data):
    """将弹幕数据添加到列表中，供前端获取"""
    danmaku_messages.append(data)
    # 只保留最新的100条消息
    if len(danmaku_messages) > 100:
        danmaku_messages.pop(0)

async def run_single_client():
    """
    演示监听一个直播间
    """
    global client, handler
    
    # 检查必要的配置是否存在
    if not all([ACCESS_KEY_ID, ACCESS_KEY_SECRET, APP_ID, ROOM_OWNER_AUTH_CODE]):
        print("Missing required environment variables")
        return

    client = blivedm.OpenLiveClient(
        access_key_id=ACCESS_KEY_ID,
        access_key_secret=ACCESS_KEY_SECRET,
        app_id=int(APP_ID),
        room_owner_auth_code=ROOM_OWNER_AUTH_CODE,
    )
    handler = DanmakuHandler(emit_danmaku)
    client.set_handler(handler)

    client.start()
    try:
        print("Danmaku client started")
        await client.join()
    finally:
        await client.stop_and_close()
        print("Danmaku client stopped")

@app.route('/messages', methods=['GET'])
def get_messages():
    """获取最新的弹幕消息"""
    return jsonify(danmaku_messages)

@app.route('/status', methods=['GET'])
def get_status():
    """获取服务状态"""
    return jsonify({
        'running': client is not None,
        'message_count': len(danmaku_messages)
    })

def run_asyncio_loop(loop):
    """在单独的线程中运行 asyncio 事件循环"""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_single_client())


if __name__ == '__main__':
    # 创建新的事件循环并在单独的线程中运行弹幕客户端
    loop = asyncio.new_event_loop()
    danmaku_thread = threading.Thread(target=run_asyncio_loop, args=(loop,))
    danmaku_thread.daemon = True
    danmaku_thread.start()
    
    # 在主线程中运行 Flask 应用
    app.run(host='localhost', port=12346, debug=True)