import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from './ui/button'
import { 
  MessageSquare, 
  Ticket, 
  FileText, 
  LogOut, 
  User,
  Menu,
  X,
  HelpCircle
} from 'lucide-react'
import { useState } from 'react'

export const Sidebar = () => {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [isCollapsed, setIsCollapsed] = useState(false)

  const navigation = [
    { 
      name: 'Chat', 
      href: '/chat', 
      icon: MessageSquare,
      description: 'AI Assistant'
    },
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

      {/* Navigation */}
      <div className="flex-1 p-4 space-y-2">
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
