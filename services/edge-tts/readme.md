# Edge TTS 服务

一个基于 edge-tts 和 Flask 的文本转语音服务，提供 REST API 接口。

## 功能

- 将文本转换为语音
- 支持多种语音（中文、英文）
- 提供 RESTful API 接口
- 返回 MP3 格式的音频文件

## 快速开始

### 环境要求

- Python 3.7+
- 虚拟环境（推荐）

### 安装

1. 创建并激活虚拟环境：
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

2. 安装依赖：
   ```bash
   pip install edge-tts flask
   ```

3. 运行服务：
   ```bash
   python edge_tts_service.py
   ```

服务将在 `http://localhost:12345` 上运行。

## API 接口

### 获取可用语音列表

```
GET /voices
```

返回系统支持的语音列表。

### 文本转语音

```
POST /tts
Content-Type: application/json

{
  "text": "需要转换的文本",
  "voice": "zh-CN-XiaoxiaoNeural"
}
```

参数说明：
- [text](file://d:\projects\airi\services\discord-bot\src\pipelines\tts.ts#L62-L62) (必需): 要转换为语音的文本
- [voice](file://d:\projects\airi\packages\stage-ui\src\components\Menu\VoiceCard.story.vue#L12-L25) (可选): 语音名称，默认为 `zh-CN-XiaoxiaoNeural`

返回：
- 成功：MP3 音频文件
- 失败：JSON 格式的错误信息

## 支持的语音

- `zh-CN-XiaoxiaoNeural` - 中文女声（晓晓）
- `zh-CN-YunyangNeural` - 中文男声（云扬）
- `en-US-JennyNeural` - 英文女声（Jenny）
- `en-US-GuyNeural` - 英文男声（Guy）

## 使用示例

### curl 示例

获取语音列表：
```bash
curl http://localhost:12345/voices
```

文本转语音：
```bash
curl -X POST http://localhost:12345/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界！", "voice": "zh-CN-XiaoxiaoNeural"}' \
  --output output.mp3
```

## 注意事项

- 服务需要网络连接才能工作
- 生成的临时文件会在系统临时目录中自动清理
