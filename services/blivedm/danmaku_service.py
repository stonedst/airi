# -*- coding: utf-8 -*-
import asyncio
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import blivedm
import blivedm.models.open_live as open_models
import blivedm.models.web as web_models

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

# Airi API endpoint
AIRI_DANMAKU_API = "http://localhost:5173/api/danmaku"

# 全局变量存储客户端和处理器
client = None
handler = None

class DanmakuHandler(blivedm.BaseHandler):
    def __init__(self, emit_callback):
        self.emit_callback = emit_callback

    def _on_open_live_danmaku(self, client: blivedm.OpenLiveClient, message: open_models.DanmakuMessage):
        danmaku_data = {
            'type': 'danmaku',
            'uname': message.uname,
            'msg': message.msg,
            'uid': message.uid,
            'room_id': message.room_id,
            'timestamp': message.timestamp,
        }
        self.emit_callback(danmaku_data)
        
        # 异步发送弹幕到Airi
        asyncio.create_task(send_danmaku_to_airi(danmaku_data))

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
        
        # 发送礼物信息到Airi
        asyncio.create_task(send_danmaku_to_airi(gift_data))

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
        
        # 发送大航海信息到Airi
        asyncio.create_task(send_danmaku_to_airi(guard_data))

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
        
        # 发送醒目留言到Airi
        asyncio.create_task(send_danmaku_to_airi(sc_data))

    def _on_open_live_like(self, client: blivedm.OpenLiveClient, message: open_models.LikeMessage):
        like_data = {
            'type': 'like',
            'uname': message.uname,
            'uid': message.uid,
            'room_id': message.room_id,
            'timestamp': message.timestamp,
        }
        self.emit_callback(like_data)
        
        # 发送点赞信息到Airi
        asyncio.create_task(send_danmaku_to_airi(like_data))

# 存储最新的弹幕消息
danmaku_messages = []

def emit_danmaku(data):
    """将弹幕数据添加到列表中，供前端获取"""
    danmaku_messages.append(data)
    # 只保留最新的100条消息
    if len(danmaku_messages) > 100:
        danmaku_messages.pop(0)

async def send_danmaku_to_airi(danmaku_data):
    """将弹幕发送到Airi系统"""
    try:
        # 构造发送给Airi的数据
        airi_data = {
            'uname': danmaku_data.get('uname', 'Unknown'),
            'msg': danmaku_data.get('msg') or danmaku_data.get('message') or 
                  f"收到{danmaku_data.get('type', 'event')}: {danmaku_data.get('gift_name', '')}",
            'uid': danmaku_data.get('uid', 0),
            'room_id': danmaku_data.get('room_id', 0),
            'timestamp': danmaku_data.get('timestamp', 0),
            'type': danmaku_data.get('type', 'unknown')
        }
        
        # 发送到Airi API
        response = requests.post(
            AIRI_DANMAKU_API,
            json=airi_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"Failed to send danmaku to AIRI: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending danmaku to AIRI: {e}")

@app.route('/configure', methods=['POST'])
def configure():
    global client, handler
    
    # 如果已有客户端在运行，先停止它
    if client is not None:
        asyncio.run(stop_client())
    
    data = request.json
    access_key_id = data.get('ACCESS_KEY_ID')
    access_key_secret = data.get('ACCESS_KEY_SECRET')
    app_id = data.get('APP_ID')
    room_owner_auth_code = data.get('ROOM_OWNER_AUTH_CODE')
    
    if not all([access_key_id, access_key_secret, app_id, room_owner_auth_code]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # 创建新的客户端
    client = blivedm.OpenLiveClient(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        app_id=int(app_id),
        room_owner_auth_code=room_owner_auth_code,
    )
    handler = DanmakuHandler(emit_danmaku)
    client.set_handler(handler)
    
    # 启动客户端
    asyncio.run(start_client())
    
    return jsonify({'status': 'success', 'message': 'Danmaku service configured and started'})

async def start_client():
    global client
    client.start()
    await client.join()

async def stop_client():
    global client, handler
    if client:
        await client.stop_and_close()
        if handler:
            handler.close()
        client = None
        handler = None

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

@app.route('/stop', methods=['POST'])
def stop():
    """停止弹幕服务"""
    global client, handler
    if client is not None:
        asyncio.run(stop_client())
        return jsonify({'status': 'success', 'message': 'Danmaku service stopped'})
    else:
        return jsonify({'status': 'error', 'message': 'Danmaku service not running'})

if __name__ == '__main__':
    app.run(host='localhost', port=12346, debug=True)