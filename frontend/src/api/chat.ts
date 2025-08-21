import { apiClient } from './client'

export interface ChatStartResponse {
  session_id: string
}

export interface ChatMessage {
  session_id: string
  message: string
}

export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  message_metadata?: any
  created_at: string
}

export interface Conversation {
  id: number
  user_id: number
  session_id: string
  created_at: string
  messages: Message[]
}

export interface ChatResponse {
  reply: string
  citations: Array<{ filename: string }>
}

export const chatApi = {
  startConversation: async (): Promise<ChatStartResponse> => {
    const response = await apiClient.post('/chat/start')
    return response.data
  },

  sendMessage: async (chatMessage: ChatMessage): Promise<ChatResponse> => {
    const response = await apiClient.post('/chat/message', chatMessage)
    return response.data
  },

  getConversationHistory: async (sessionId: string): Promise<Conversation> => {
    const response = await apiClient.get(`/chat/${sessionId}/history`)
    return response.data
  },

  // Get user's conversations list
  getUserConversations: async (): Promise<Conversation[]> => {
    const response = await apiClient.get('/chat/conversations')
    return response.data
  },
}
