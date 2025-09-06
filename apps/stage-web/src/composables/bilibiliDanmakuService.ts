import { useStorage } from '@vueuse/core'
import { ref } from 'vue'

import { useDanmakuHandler } from './danmakuHandler'

// 弹幕消息类型定义
export interface DanmakuMessage {
  type: string
  uname: string
  msg?: string
  message?: string
  uid: number
  room_id: number
  timestamp: number
  gift_name?: string
  gift_num?: number
  guard_name?: string
}

// 弹幕服务状态
export interface DanmakuServiceStatus {
  running: boolean
  message_count: number
}

// 弹幕轮询器
export function useBilibiliDanmakuPolling() {
  const danmakuHandler = useDanmakuHandler()

  // 从存储中获取弹幕服务配置
  const danmakuServiceConfig = useStorage('bilibili-danmaku-config', {
    baseUrl: 'http://localhost:12346/',
    ACCESS_KEY_ID: '',
    ACCESS_KEY_SECRET: '',
    APP_ID: '',
    ROOM_OWNER_AUTH_CODE: '',
  })

  // 轮询状态
  const isPolling = ref(false)
  const pollingInterval = ref<number | null>(null)
  const lastProcessedTimestamp = useStorage('bilibili-danmaku-last-timestamp', 0)

  // 错误状态
  const error = ref<string | null>(null)

  // 获取弹幕服务状态
  async function getServiceStatus(): Promise<DanmakuServiceStatus | null> {
    try {
      const response = await fetch(`${danmakuServiceConfig.value.baseUrl}status`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    }
    catch (err) {
      error.value = `获取弹幕服务状态失败: ${err}`
      console.error('获取弹幕服务状态失败:', err)
      return null
    }
  }

  // 配置并启动弹幕服务
  async function configureAndStartService(): Promise<boolean> {
    try {
      const response = await fetch(`${danmakuServiceConfig.value.baseUrl}configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ACCESS_KEY_ID: danmakuServiceConfig.value.ACCESS_KEY_ID,
          ACCESS_KEY_SECRET: danmakuServiceConfig.value.ACCESS_KEY_SECRET,
          APP_ID: danmakuServiceConfig.value.APP_ID,
          ROOM_OWNER_AUTH_CODE: danmakuServiceConfig.value.ROOM_OWNER_AUTH_CODE,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      if (result.status === 'success') {
        error.value = null
        return true
      }
      else {
        throw new Error(result.message || '配置弹幕服务失败')
      }
    }
    catch (err) {
      error.value = `配置弹幕服务失败: ${err}`
      console.error('配置弹幕服务失败:', err)
      return false
    }
  }

  // 获取最新的弹幕消息
  async function fetchDanmakuMessages(): Promise<DanmakuMessage[] | null> {
    try {
      const response = await fetch(`${danmakuServiceConfig.value.baseUrl}messages`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    }
    catch (err) {
      error.value = `获取弹幕消息失败: ${err}`
      console.error('获取弹幕消息失败:', err)
      return null
    }
  }

  // 处理单条弹幕消息
  async function processDanmakuMessage(message: DanmakuMessage) {
    // 只处理新消息（根据时间戳判断）
    if (message.timestamp <= lastProcessedTimestamp.value) {
      return
    }

    try {
      // 更新最后处理的时间戳
      lastProcessedTimestamp.value = message.timestamp

      // 构造消息内容
      let content = ''
      switch (message.type) {
        case 'danmaku':
          content = message.msg || ''
          break
        case 'gift':
          content = `赠送 ${message.gift_name} x${message.gift_num}`
          break
        case 'guard':
          content = `购买大航海: ${message.guard_name}`
          break
        case 'superchat':
          content = `醒目留言: ${message.message}`
          break
        case 'like':
          content = '点赞'
          break
        default:
          content = message.message || message.msg || `收到${message.type}事件`
      }

      // 使用现有的弹幕处理器处理消息
      await danmakuHandler.handleDanmaku({
        uname: message.uname,
        msg: content,
        uid: message.uid,
        room_id: message.room_id,
        timestamp: message.timestamp,
        type: message.type,
      })
    }
    catch (err) {
      console.error('处理弹幕消息失败:', err)
    }
  }

  // 轮询弹幕消息
  async function pollDanmakuMessages() {
    const messages = await fetchDanmakuMessages()
    if (messages && messages.length > 0) {
      // 按时间戳排序并处理消息
      messages.sort((a, b) => a.timestamp - b.timestamp)
      for (const message of messages) {
        await processDanmakuMessage(message)
      }
    }
  }

  // 开始轮询
  function startPolling(interval: number = 3000) {
    if (isPolling.value) {
      return
    }

    isPolling.value = true
    pollingInterval.value = window.setInterval(async () => {
      await pollDanmakuMessages()
    }, interval)
  }

  // 停止轮询
  function stopPolling() {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
    isPolling.value = false
  }

  // 停止弹幕服务
  async function stopService(): Promise<boolean> {
    try {
      const response = await fetch(`${danmakuServiceConfig.value.baseUrl}stop`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      if (result.status === 'success') {
        stopPolling()
        error.value = null
        return true
      }
      else {
        throw new Error(result.message || '停止弹幕服务失败')
      }
    }
    catch (err) {
      error.value = `停止弹幕服务失败: ${err}`
      console.error('停止弹幕服务失败:', err)
      return false
    }
  }

  return {
    // 状态
    isPolling,
    error,
    lastProcessedTimestamp,
    danmakuServiceConfig,

    // 方法
    getServiceStatus,
    configureAndStartService,
    fetchDanmakuMessages,
    processDanmakuMessage,
    pollDanmakuMessages,
    startPolling,
    stopPolling,
    stopService,
  }
}
