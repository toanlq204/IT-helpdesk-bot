import { Card, CardContent, CardHeader } from './ui/card'
import { Badge } from './ui/badge'
import { Ticket } from '../api/tickets'
import { useAuth } from '../hooks/useAuth'
import { formatDistanceToNow } from 'date-fns'

interface TicketCardProps {
  ticket: Ticket
  onClick: () => void
}

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'low':
      return 'bg-green-100 text-green-800 border-green-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'open':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'in_progress':
      return 'bg-orange-100 text-orange-800 border-orange-200'
    case 'resolved':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'closed':
      return 'bg-gray-100 text-gray-800 border-gray-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

export const TicketCard = ({ ticket, onClick }: TicketCardProps) => {
  const { user } = useAuth()

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h3 className="font-semibold text-lg">{ticket.title}</h3>
            <p className="text-sm text-gray-600">#{ticket.id}</p>
          </div>
          <div className="flex gap-2">
            <Badge className={getPriorityColor(ticket.priority)}>
              {ticket.priority}
            </Badge>
            <Badge className={getStatusColor(ticket.status)}>
              {ticket.status.replace('_', ' ')}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-700 mb-4 line-clamp-2">{ticket.description}</p>
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Created {formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}
          </span>
          {ticket.assigned_to && (
            <span>
              Assigned {ticket.assigned_to === user?.id ? 'to you' : `to user #${ticket.assigned_to}`}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
