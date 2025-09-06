// 弹幕处理 Composable
import { useChatStore } from '@proj-airi/stage-ui/stores/chat'
import { useConsciousnessStore } from '@proj-airi/stage-ui/stores/modules/consciousness'
import { useProvidersStore } from '@proj-airi/stage-ui/stores/providers'
import { storeToRefs } from 'pinia'

export function useDanmakuHandler() {
  const chatStore = useChatStore()
  const consciousnessStore = useConsciousnessStore()
  const providersStore = useProvidersStore()
  const { activeProvider, activeModel } = storeToRefs(consciousnessStore)

  /**
   * 处理来自B站的弹幕消息
   * @param danmakuData 弹幕数据
   * @param danmakuData.uname 用户名
   * @param danmakuData.msg 弹幕消息内容
   * @param danmakuData.uid 用户ID
   * @param danmakuData.room_id 直播间ID
   * @param danmakuData.timestamp 时间戳
   * @param danmakuData.type 消息类型
   */
  async function handleDanmaku(danmakuData: {
    uname: string
    msg: string
    uid: number
    room_id: number
    timestamp: number
    type?: string
  }) {
    try {
      // 构造用户消息
      const userMessage = `[B站弹幕] ${danmakuData.uname}: ${danmakuData.msg}`

      // 使用 handleExternalMessage 方法添加到聊天记录中，支持 metadata
      await chatStore.handleExternalMessage(userMessage, {
        source: 'bilibili_danmaku',
        uid: danmakuData.uid,
        uname: danmakuData.uname,
        room_id: danmakuData.room_id,
        timestamp: danmakuData.timestamp,
        type: danmakuData.type || 'danmaku',
      })

      // 自动触发AI回复
      await triggerAIResponse(userMessage)
    }
    catch (error) {
      console.error('Error handling danmaku:', error)
      throw error
    }
  }

  /**
   * 触发AI回复
   */
  async function triggerAIResponse(userMessage: string) {
    try {
      const providerConfig = providersStore.getProviderConfig(activeProvider.value)

      await chatStore.send(userMessage, {
        chatProvider: await providersStore.getProviderInstance(activeProvider.value),
        model: activeModel.value,
        providerConfig,
      })
    }
    catch (error) {
      console.error('Error triggering AI response for danmaku:', error)
      // 添加错误消息到聊天记录
      chatStore.messages.push({
        role: 'error',
        content: `处理弹幕消息时出错: ${(error as Error).message}`,
      })
    }
  }

  return {
    handleDanmaku,
    triggerAIResponse,
  }
}
