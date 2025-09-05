# edge_tts_service.py
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS  # 新增导入
import edge_tts
import asyncio
import io
import tempfile
import os

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])  # 允许指定来源


# 预定义的声音列表
VOICES = [
    {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao (Chinese)", "languages": [{"code": "zh", "title": "Chinese"}]},
    {"id": "zh-CN-YunyangNeural", "name": "Yunyang (Chinese)", "languages": [{"code": "zh", "title": "Chinese"}]},
    {"id": "en-US-JennyNeural", "name": "Jenny (English)", "languages": [{"code": "en", "title": "English"}]},
    {"id": "en-US-GuyNeural", "name": "Guy (English)", "languages": [{"code": "en", "title": "English"}]},
]

@app.route('/voices', methods=['GET'])
def list_voices():
    return jsonify(VOICES)

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')
    voice = data.get('voice', 'zh-CN-XiaoxiaoNeural')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # 使用 edge-tts 生成音频
    async def generate_audio():
        communicate = edge_tts.Communicate(text, voice)
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_filename = temp_file.name
        temp_file.close()
        
        await communicate.save(temp_filename)
        return temp_filename
    
    try:
        # 运行异步函数
        temp_filename = asyncio.run(generate_audio())
        return send_file(temp_filename, mimetype='audio/mpeg', as_attachment=True, download_name='speech.mp3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/speech', methods=['POST'])
def audio_speech():
    data = request.json
    model = data.get('model', '')
    text = data.get('input', '')
    voice = data.get('voice', 'zh-CN-XiaoxiaoNeural')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # 使用 edge-tts 生成音频
    async def generate_audio():
        communicate = edge_tts.Communicate(text, voice)
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_filename = temp_file.name
        temp_file.close()
        
        await communicate.save(temp_filename)
        return temp_filename
    
    try:
        # 运行异步函数
        temp_filename = asyncio.run(generate_audio())
        return send_file(temp_filename, mimetype='audio/mpeg', as_attachment=True, download_name='speech.mp3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='localhost', port=12345, debug=True)