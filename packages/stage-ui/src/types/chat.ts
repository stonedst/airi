import type { AssistantMessage, CommonContentPart, CompletionToolCall, SystemMessage, ToolMessage, UserMessage } from '@xsai/shared-chat'

export interface ChatSlicesText {
  type: 'text'
  text: string
}

export interface ChatSlicesToolCall {
  type: 'tool-call'
  toolCall: CompletionToolCall
}

export interface ChatSlicesToolCallResult {
  type: 'tool-call-result'
  id: string
  result?: string | CommonContentPart[]
}

export type ChatSlices = ChatSlicesText | ChatSlicesToolCall | ChatSlicesToolCallResult

export interface ChatAssistantMessage extends AssistantMessage {
  slices: ChatSlices[]
  tool_results: {
    id: string
    result?: string | CommonContentPart[]
  }[]
}

// 扩展 UserMessage 类型以支持 metadata
export interface ChatUserMessage extends UserMessage {
  metadata?: Record<string, any>
}

export type ChatMessage = ChatAssistantMessage | SystemMessage | ToolMessage | UserMessage | ChatUserMessage
