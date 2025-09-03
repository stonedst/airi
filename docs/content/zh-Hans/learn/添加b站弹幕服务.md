# 如何在 AIRI 项目中添加 B站弹幕服务

AIRI 项目是一个开源的 AI 虚拟角色项目，支持多种平台的集成。如果你想添加一个 B站弹幕服务，用于获取弹幕并将其发送到 AIRI 的 LLM 中进行处理，可以按照以下步骤操作。

## 1. 创建新的服务目录

首先，在 `services` 目录下创建一个新的服务目录：

```bash
mkdir services/bilibili-danmaku
cd services/bilibili-danmaku
```

## 2. 初始化项目

创建 [package.json](file://d:\projects\airi\package.json) 文件：

```json
{
  "name": "@proj-airi/bilibili-danmaku",
  "type": "module",
  "private": true,
  "description": "Bilibili danmaku service for AIRI",
  "author": {
    "name": "Moeru AI Project AIRI Team",
    "email": "airi@moeru.ai",
    "url": "https://github.com/moeru-ai"
  },
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/moeru-ai/airi.git",
    "directory": "services/bilibili-danmaku"
  },
  "scripts": {
    "start": "dotenvx run -f .env -f .env.local --overload --ignore=MISSING_ENV_FILE -- tsx src/index.ts",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@dotenvx/dotenvx": "^1.49.0",
    "@guiiai/logg": "^1.0.10",
    "@proj-airi/server-sdk": "workspace:^",
    "bilibili-live-danmaku": "^1.0.0"
  },
  "devDependencies": {
    "tsx": "^4.7.1",
    "typescript": "~5.4.2"
  }
}
```

## 3. 安装依赖包

根据搜索结果，可以使用 `bilibili-live-danmaku` 或类似的 npm 包来获取 B站弹幕。在 `dependencies` 中添加相关依赖。

## 4. 创建服务代码

创建 `src/index.ts` 文件：

```typescript
import { env } from 'node:process'

import { Format, LogLevel, setGlobalFormat, setGlobalLogLevel, useLogg } from '@guiiai/logg'
import { Client as AiriClient } from '@proj-airi/server-sdk'
// 假设使用 bili-live-listener 包来监听弹幕
import { BiliLive } from 'bili-live-listener'

setGlobalFormat(Format.Pretty)
setGlobalLogLevel(LogLevel.Log)
const log = useLogg('Bilibili-Danmaku').useGlobalConfig()

interface DanmakuMessage {
  user: {
    uid: number
    uname: string
  }
  content: string
  timestamp: number
}

async function main() {
  // 创建 AIRI 客户端
  const airiClient = new AiriClient({
    name: 'bilibili-danmaku',
    possibleEvents: ['input:text'],
    token: env.AIRI_TOKEN || 'default-token'
  })

  // 连接到 AIRI 核心服务
  await airiClient.connect()

  // 获取直播间ID（从环境变量或配置文件中）
  const roomId = Number.parseInt(env.BILIBILI_ROOM_ID || '0')
  if (!roomId) {
    log.error('请设置 BILIBILI_ROOM_ID 环境变量')
    process.exit(1)
  }

  // 创建 B站直播监听器
  const biliLive = new BiliLive(roomId, {
    key: env.BILIBILI_KEY,
    uid: Number.parseInt(env.BILIBILI_UID || '0'),
  })

  // 监听弹幕消息
  biliLive.onDanmu(({ data }) => {
    const danmaku: DanmakuMessage = {
      user: data.user,
      content: data.content,
      timestamp: Date.now()
    }

    log.log(`收到弹幕: ${danmaku.user.uname}: ${danmaku.content}`)

    // 处理弹幕（例如过滤、格式化等）
    const processedContent = processDanmaku(danmaku)

    // 将弹幕发送到 AIRI 的 LLM 进行处理
    airiClient.emit('input:text', {
      text: processedContent,
      metadata: {
        source: 'bilibili',
        user: danmaku.user.uname,
        timestamp: danmaku.timestamp
      }
    })
  })

  // 监听礼物消息
  biliLive.onGift(({ data }) => {
    log.log(`收到礼物: ${data.user.uname} 赠送 ${data.gift.name} x${data.gift.num}`)

    // 可以将礼物信息也发送给 AIRI 进行处理
    airiClient.emit('input:text', {
      text: `${data.user.uname} 赠送 ${data.gift.name} x${data.gift.num}`,
      metadata: {
        source: 'bilibili-gift',
        user: data.user.uname,
        gift: data.gift.name,
        count: data.gift.num
      }
    })
  })

  // 错误处理
  biliLive.onError((error) => {
    log.error('B站直播监听器错误:', error)
  })

  log.log(`开始监听 B站直播间 ${roomId} 的弹幕`)
}

// 处理弹幕的函数
function processDanmaku(danmaku: DanmakuMessage): string {
  // 这里可以添加弹幕过滤、格式化等处理逻辑
  // 例如：过滤掉特定关键词、格式化用户名等

  // 简单示例：添加用户名前缀
  return `[B站] ${danmaku.user.uname}: ${danmaku.content}`
}

main().catch(err => log.withError(err).error('发生错误'))

// 优雅关闭
process.on('SIGINT', () => {
  log.log('正在关闭服务...')
  process.exit(0)
})

process.on('SIGTERM', () => {
  log.log('正在关闭服务...')
  process.exit(0)
})
```

## 5. 配置环境变量

创建 `.env` 文件：

```env
# AIRI 配置
AIRI_TOKEN=your_airi_token
AIRI_SERVER_URL=ws://localhost:8080

# B站配置
BILIBILI_ROOM_ID=123456
BILIBILI_KEY=your_bilibili_key
BILIBILI_UID=your_bilibili_uid
```

## 6. 添加到项目构建系统

确保在根目录的 [pnpm-workspace.yaml](file://d:\projects\airi\pnpm-workspace.yaml) 中包含了新服务：

```yaml
packages:
  - packages/**
  - plugins/**
  - services/**
  - examples/**
  - docs/**
  - apps/**
  - '!**/dist/**'
```

## 7. 更新根目录的 package.json

在根目录的 `package.json` 中添加启动脚本：

```json
{
  "scripts": {
    "dev:bilibili": "pnpm -rF @proj-airi/bilibili-danmaku run start",
    "start:bilibili": "pnpm -rF @proj-airi/bilibili-danmaku run start"
  }
}
```

## 8. 实现弹幕处理逻辑

根据你的具体需求，可以在 `processDanmaku` 函数中实现弹幕处理逻辑，例如：

1. 过滤掉特定关键词的弹幕
2. 对特定用户进行特殊处理
3. 将弹幕分类（如问题、评论、表情等）
4. 进行情感分析
5. 合并相似弹幕

## 9. 测试和运行

安装依赖并启动服务：

```bash
pnpm install
pnpm dev:bilibili
```

## 注意事项

1. **API 限制**：B站可能对弹幕获取有频率限制，需要合理处理。
2. **认证**：某些功能可能需要 B站账号认证。
3. **错误处理**：网络波动可能导致连接中断，需要实现重连机制。
4. **性能**：高人气直播间弹幕量大，需要注意性能优化。
5. **合规性**：确保遵守 B站的使用条款和相关法律法规。

通过以上步骤，你就可以在 AIRI 项目中添加一个 B站弹幕服务，将弹幕实时发送到 AIRI 的 LLM 中进行处理了。
```

这个方案基于 AIRI 项目现有的架构模式，参考了 discord-bot 和 telegram-bot 的实现方式，并结合了 Node.js 生态中可用的 B站弹幕监听库。你可以根据实际需求和选择的具体 npm 包来调整代码实现。
