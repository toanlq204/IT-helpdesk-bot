import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useChat } from '../hooks/useChat'
import { Button } from './ui/button'
import { 
  MessageSquare, 
  Ticket, 
  FileText, 
  LogOut, 
  User,
  Menu,
  X,
  HelpCircle,
  Plus,
  Clock
} from 'lucide-react'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

export const Sidebar = () => {
  const { user, logout } = useAuth()
  const { conversations, startConversation, isStarting } = useChat()
  const location = useLocation()
  const navigate = useNavigate()
  const [isCollapsed, setIsCollapsed] = useState(false)

  const navigation = [
    { 
      name: 'Tickets', 
      href: '/tickets', 
      icon: Ticket,
      description: 'Support Tickets'
    },
    ...(user?.role === 'admin' ? [{
      name: 'Documents', 
      href: '/documents', 
      icon: FileText,
      description: 'Knowledge Base'
    }] : []),
  ]

  const handleNewChat = async () => {
    try {
      const result = await startConversation()
      navigate(`/chat?session=${result.session_id}`)
    } catch (error) {
      console.error('Failed to start conversation:', error)
      // Fallback to regular chat page
      navigate('/chat')
    }
  }

  const getConversationTitle = (conversation: any) => {
    // Use the first user message as the conversation title
    const firstUserMessage = conversation.messages?.find((msg: any) => msg.role === 'user')
    if (!firstUserMessage) return 'New conversation'
    
    const title = firstUserMessage.content.trim()
    return title.length > 40 ? title.substring(0, 40) + '...' : title
  }

  const getConversationPreview = (conversation: any) => {
    const lastMessage = conversation.messages?.[conversation.messages.length - 1]
    if (!lastMessage) return 'Start a conversation'
    
    // Show preview of the last message
    const preview = lastMessage.role === 'user' 
      ? lastMessage.content 
      : lastMessage.content
    
    return preview.length > 35 ? preview.substring(0, 35) + '...' : preview
  }

  const isActive = (href: string) => {
    return location.pathname === href || location.pathname.startsWith(href + '/')
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-500/20 text-red-300 border-red-500/30'
      case 'technician':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
      case 'user':
        return 'bg-green-500/20 text-green-300 border-green-500/30'
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
    }
  }

  return (
    <div className={`h-screen bg-[hsl(var(--sidebar-background))] border-r border-border flex flex-col transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              <HelpCircle className="w-8 h-8 text-primary" />
              <div>
                <h1 className="text-lg font-bold text-foreground">IT Helpdesk</h1>
                <p className="text-xs text-muted-foreground">Support Center</p>
              </div>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-muted-foreground hover:text-foreground"
          >
            {isCollapsed ? <Menu className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4 border-b border-border">
        <Button
          onClick={handleNewChat}
          disabled={isStarting}
          className={`w-full justify-start ${isCollapsed ? 'px-2' : ''}`}
          variant="outline"
        >
          <Plus className="w-4 h-4 flex-shrink-0" />
          {!isCollapsed && <span className="ml-2">New Chat</span>}
        </Button>
      </div>

      {/* Conversations List */}
      {!isCollapsed && (
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="px-4 py-2">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Recent Conversations
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto px-4 space-y-1 scrollbar-hide">
            {conversations.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No conversations yet</p>
                <p className="text-xs text-muted-foreground">Start a new chat to begin</p>
              </div>
            ) : (
              conversations.map((conversation) => {
                const isActive = location.pathname === '/chat' && 
                  new URLSearchParams(location.search).get('session') === conversation.session_id
                
                return (
                  <Link
                    key={conversation.id}
                    to={`/chat?session=${conversation.session_id}`}
                    className={`block rounded-lg p-3 transition-all duration-200 group ${
                      isActive 
                        ? 'bg-primary/10 text-primary border border-primary/20' 
                        : 'text-muted-foreground hover:text-foreground hover:bg-[hsl(var(--sidebar-hover))]'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <MessageSquare className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate leading-tight">
                          {getConversationTitle(conversation)}
                        </p>
                        <p className="text-xs text-muted-foreground truncate mt-1">
                          {getConversationPreview(conversation)}
                        </p>
                        {/* <div className="flex items-center mt-1 text-xs text-muted-foreground">
                          <Clock className="w-3 h-3 mr-1" />
                          <span>
                            {formatDistanceToNow(new Date(conversation.created_at), { addSuffix: true })}
                          </span>
                        </div> */}
                      </div>
                    </div>
                  </Link>
                )
              })
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="border-t border-border p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          const active = isActive(item.href)
          
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`block rounded-lg transition-all duration-200 ${
                active 
                  ? 'bg-primary/10 text-primary border border-primary/20' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-[hsl(var(--sidebar-hover))]'
              }`}
            >
              <div className={`flex items-center p-3 ${isCollapsed ? 'justify-center' : 'space-x-3'}`}>
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <p className="font-medium">{item.name}</p>
                    <p className="text-xs text-muted-foreground">{item.description}</p>
                  </div>
                )}
              </div>
            </Link>
          )
        })}
      </div>

      {/* User Section */}
      <div className="p-4 border-t border-border">
        {!isCollapsed && (
          <div className="space-y-3">
            {/* User Info */}
            <div className="flex items-center space-x-3 p-3 rounded-lg bg-[hsl(var(--sidebar-hover))]">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  {user?.email}
                </p>
                <div className="flex items-center mt-1">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getRoleBadgeColor(user?.role || '')}`}>
                    {user?.role}
                  </span>
                </div>
              </div>
            </div>

            {/* Logout Button */}
            <Button
              variant="outline"
              className="w-full justify-start text-muted-foreground hover:text-foreground border-border/50"
              onClick={logout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        )}
        
        {isCollapsed && (
          <div className="space-y-2">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
              <User className="w-4 h-4 text-primary" />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="w-full justify-center text-muted-foreground hover:text-foreground"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
