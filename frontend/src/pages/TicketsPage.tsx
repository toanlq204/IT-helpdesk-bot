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
    <div className="h-full flex flex-col bg-background">
      <div className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Tickets</h1>
              <p className="text-muted-foreground">Manage support tickets</p>
            </div>
            <CreateTicketDialog />
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">

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
    </div>
  )
}
