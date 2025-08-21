import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi, ChatMessage, Conversation } from '../api/chat'

export const useChat = () => {
  const queryClient = useQueryClient()

  const conversationsQuery = useQuery({
    queryKey: ['conversations'],
    queryFn: chatApi.getUserConversations,
  })

  const startConversationMutation = useMutation({
    mutationFn: chatApi.startConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const sendMessageMutation = useMutation({
    mutationFn: chatApi.sendMessage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  return {
    conversations: conversationsQuery.data || [],
    isLoading: conversationsQuery.isLoading,
    error: conversationsQuery.error,
    startConversation: startConversationMutation.mutateAsync,
    sendMessage: sendMessageMutation.mutateAsync,
    isStarting: startConversationMutation.isPending,
    isSending: sendMessageMutation.isPending,
  }
}

export const useConversation = (sessionId: string) => {
  const conversationQuery = useQuery({
    queryKey: ['conversation', sessionId],
    queryFn: () => chatApi.getConversationHistory(sessionId),
    enabled: !!sessionId,
  })

  return {
    conversation: conversationQuery.data,
    isLoading: conversationQuery.isLoading,
    error: conversationQuery.error,
    refetch: conversationQuery.refetch,
  }
}
