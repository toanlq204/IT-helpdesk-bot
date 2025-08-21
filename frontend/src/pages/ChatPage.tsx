import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Send } from 'lucide-react'

// TODO: streaming handling

export const ChatPage = () => {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Array<{
    id: string
    role: 'user' | 'assistant'
    content: string
    citations?: Array<{ filename: string }>
  }>>([])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: message
    }

    setMessages(prev => [...prev, userMessage])
    setMessage('')

    // TODO: Replace with actual API call
    setTimeout(() => {
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: `🔧 Placeholder response:\n• You said: "${message}"\n• I'll use your uploaded documents to answer once RAG is connected.\n• Potential sources:\n  - sample_guide.txt`,
        citations: [{ filename: 'sample_guide.txt' }]
      }
      setMessages(prev => [...prev, assistantMessage])
    }, 1000)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chat Assistant</h1>
        <p className="text-gray-600">Ask questions about IT support and troubleshooting</p>
      </div>

      <Card className="flex-1 flex flex-col">
        <CardHeader>
          <CardTitle>Conversation</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 space-y-4 mb-4 overflow-y-auto max-h-96">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                Start a conversation by typing a message below
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {msg.citations.map((citation, index) => (
                          <span
                            key={index}
                            className="inline-block px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded"
                          >
                            {citation.filename}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Message Input */}
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1"
            />
            <Button type="submit" disabled={!message.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
