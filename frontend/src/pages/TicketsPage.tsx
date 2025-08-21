import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { CreateTicketDialog } from '../components/CreateTicketDialog'
import { TicketCard } from '../components/TicketCard'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { useTickets } from '../hooks/useTickets'
import { useAuth } from '../hooks/useAuth'

export const TicketsPage = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { tickets, unassignedTickets, assignedTickets, isLoading } = useTickets()
  const [activeTab, setActiveTab] = useState<'all' | 'unassigned' | 'assigned'>('all')

  const getTicketsToShow = () => {
    if (user?.role === 'user') {
      return tickets.filter(ticket => ticket.created_by === user.id)
    }
    
    switch (activeTab) {
      case 'unassigned':
        return unassignedTickets
      case 'assigned':
        return assignedTickets
      default:
        return tickets
    }
  }

  const ticketsToShow = getTicketsToShow()

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tickets</h1>
          <p className="text-gray-600">Manage support tickets</p>
        </div>
        <CreateTicketDialog />
      </div>

      {/* Tabs for technicians and admins */}
      {user?.role !== 'user' && (
        <div className="flex space-x-1 mb-6">
          <Button
            variant={activeTab === 'all' ? 'default' : 'outline'}
            onClick={() => setActiveTab('all')}
          >
            All Tickets
          </Button>
          <Button
            variant={activeTab === 'unassigned' ? 'default' : 'outline'}
            onClick={() => setActiveTab('unassigned')}
          >
            Unassigned
          </Button>
          <Button
            variant={activeTab === 'assigned' ? 'default' : 'outline'}
            onClick={() => setActiveTab('assigned')}
          >
            Assigned to Me
          </Button>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>
            {user?.role === 'user' 
              ? 'My Tickets' 
              : activeTab === 'all' 
                ? 'All Tickets'
                : activeTab === 'unassigned'
                  ? 'Unassigned Tickets'
                  : 'Assigned to Me'
            }
          </CardTitle>
        </CardHeader>
        <CardContent>
          {ticketsToShow.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No tickets found. {user?.role === 'user' ? 'Create your first ticket to get started.' : 'No tickets match the current filter.'}
            </div>
          ) : (
            <div className="space-y-4">
              {ticketsToShow.map((ticket) => (
                <TicketCard
                  key={ticket.id}
                  ticket={ticket}
                  onClick={() => navigate(`/tickets/${ticket.id}`)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
