import { useState, useRef, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Textarea } from '../components/ui/textarea'
import { Send, Bot, User, FileText, Sparkles } from 'lucide-react'
import { useConversation, useChat } from '../hooks/useChat'
import { MarkdownMessage } from '../components/MarkdownMessage'

// TODO: streaming handling

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Array<{ filename: string }>
  timestamp: Date
}

export const ChatPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('session')
  const { conversation, refetch } = useConversation(sessionId || '')
  const { startConversation, sendMessage, isSending } = useChat()
  
  const [message, setMessage] = useState('')
  const [localMessages, setLocalMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Convert backend messages to local format and combine with local messages
  const serverMessages = conversation?.messages?.map(msg => ({
    id: msg.id.toString(),
    role: msg.role as 'user' | 'assistant',
    content: msg.content,
    citations: msg.message_metadata?.citations || [],
    timestamp: new Date(msg.created_at)
  })) || []

  // Combine server messages with local messages (local messages for immediate feedback)
  // If we have server messages, use them as the base and add any local messages that aren't duplicates
  const messages = sessionId && serverMessages.length > 0 
    ? [...serverMessages, ...localMessages.filter(localMsg => 
        !serverMessages.some(serverMsg => serverMsg.content === localMsg.content)
      )]
    : localMessages

  // Generate conversation title from first user message
  const getConversationTitle = () => {
    if (!sessionId) return 'New Chat'
    
    const firstUserMessage = messages.find(msg => msg.role === 'user')
    if (!firstUserMessage) return 'New Conversation'
    
    // Use first 50 characters of the first message as title
    const title = firstUserMessage.content.trim()
    return title.length > 50 ? title.substring(0, 50) + '...' : title
  }

  const conversationTitle = getConversationTitle()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Clear local messages when switching conversations
  useEffect(() => {
    setLocalMessages([])
  }, [sessionId])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || isSending) return

    const messageText = message
    setMessage('')

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    // Create user message and add it immediately (optimistic UI)
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date()
    }

    // Add user message immediately to local state for instant feedback
    setLocalMessages(prev => [...prev, userMessage])

    setIsTyping(true)

    try {
      let currentSessionId = sessionId

      // If no session exists, create a new one
      if (!currentSessionId) {
        const newSession = await startConversation()
        currentSessionId = newSession.session_id
        navigate(`/chat?session=${currentSessionId}`)
      }

      // Send message to the backend
      if (currentSessionId) {
        await sendMessage({
          session_id: currentSessionId,
          message: messageText
        })

        // Refetch conversation to get updated messages (including assistant response)
        await refetch()
        
        // Clear local messages since we now have the full conversation from the server
        setLocalMessages([])
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      
      // Add error message to local state
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I'm having trouble connecting to the server. Please try again later.`,
        citations: [],
        timestamp: new Date()
      }
      
      setLocalMessages(prev => [...prev, assistantMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(e)
    }
  }

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[hsl(var(--chat-background))]">
      {/* Header */}
      <div className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-4">
                      <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-xl font-semibold text-foreground truncate">
                  {conversationTitle}
                </h1>
                <p className="text-sm text-muted-foreground">
                  {sessionId 
                    ? `IT Support Chat • ${messages.length} message${messages.length !== 1 ? 's' : ''}`
                    : 'Ask questions about IT support and troubleshooting'
                  }
                </p>
              </div>
            </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-12">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
                <Bot className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-semibold text-foreground mb-2">How can I help you today?</h2>
              <p className="text-muted-foreground text-center max-w-md">
                I'm your IT support assistant. Ask me about technical issues, software problems, or general IT guidance.
              </p>
              <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
                {[
                  "How do I reset my password?",
                  "My computer is running slowly",
                  "Help with email configuration",
                  "Network connectivity issues"
                ].map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => setMessage(prompt)}
                    className="p-3 text-left rounded-lg border border-border hover:bg-accent hover:text-accent-foreground transition-colors"
                  >
                    <span className="text-sm">{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="py-8 space-y-8">
              {messages.map((msg) => (
                <div key={msg.id} className="chat-fade-in">
                  <div className={`flex items-start space-x-4 ${
                    msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      msg.role === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-muted text-muted-foreground'
                    }`}>
                      {msg.role === 'user' ? (
                        <User className="w-4 h-4" />
                      ) : (
                        <Bot className="w-4 h-4" />
                      )}
                    </div>
                    <div className={`flex-1 min-w-0 ${
                      msg.role === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      <div className={`flex items-center space-x-2 mb-2 ${
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}>
                        <span className="text-sm font-medium text-foreground">
                          {msg.role === 'user' ? 'You' : 'AI Assistant'}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {msg.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <div className={`prose prose-sm dark:prose-invert max-w-none ${
                        msg.role === 'user' ? 'text-right' : 'text-left'
                      }`}>
                        <div className={`inline-block px-4 py-3 rounded-2xl max-w-[80%] ${
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground ml-auto'
                            : 'bg-muted text-foreground mr-auto'
                        }`}>
                          {msg.role === 'user' ? (
                            <div className="whitespace-pre-wrap leading-relaxed">
                              {msg.content}
                            </div>
                          ) : (
                            <MarkdownMessage content={msg.content} />
                          )}
                        </div>
                      </div>
                      {msg.citations && msg.citations.length > 0 && (
                        <div className={`mt-2 flex flex-wrap gap-2 ${
                          msg.role === 'user' ? 'justify-end' : 'justify-start'
                        }`}>
                          {msg.citations.map((citation: { filename: string }, index: number) => (
                            <div
                              key={index}
                              className="inline-flex items-center space-x-1 px-2 py-1 bg-muted rounded-md text-xs"
                            >
                              <FileText className="w-3 h-3" />
                              <span>{citation.filename}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {(isTyping || isSending) && (
                <div className="chat-fade-in">
                  <div className="flex items-start space-x-4">
                    <div className="w-8 h-8 rounded-lg bg-muted text-muted-foreground flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-foreground">AI Assistant</span>
                        <span className="text-xs text-muted-foreground">
                          {isSending ? 'sending...' : 'typing...'}
                        </span>
                      </div>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <form onSubmit={handleSendMessage} className="relative">
            <div className="relative flex items-end space-x-3">
              <div className="flex-1 relative">
                <Textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => {
                    setMessage(e.target.value)
                    adjustTextareaHeight()
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask anything about IT support..."
                  className="min-h-[48px] max-h-[120px] resize-none pr-12 bg-background border-border focus:ring-2 focus:ring-primary focus:border-transparent"
                  rows={1}
                />
                <Button
                  type="submit"
                  disabled={!message.trim() || isTyping || isSending}
                  size="sm"
                  className="absolute right-2 bottom-2 h-8 w-8 p-0"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </form>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Press Enter to send, Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}
