import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTicket, useTickets } from '../hooks/useTickets'
import { useAuthStore } from '../store/auth'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Textarea } from '../components/ui/textarea'
import { Label } from '../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Alert, AlertDescription } from '../components/ui/alert'
import { 
  ArrowLeft,
  Clock,
  User,
  Tag,
  AlertCircle,
  MessageSquare,
  Lock,
  Plus,
  Edit
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export const TicketDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { updateTicket, addNote, isUpdating } = useTickets()
  
  const ticketId = id ? parseInt(id) : 0
  const { ticket, isLoading, error, refetch } = useTicket(ticketId)
  
  const [isAddingNote, setIsAddingNote] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [isInternalNote, setIsInternalNote] = useState(false)
  const [isEditingStatus, setIsEditingStatus] = useState(false)
  const [newStatus, setNewStatus] = useState<string>('')

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate('/tickets')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tickets
          </Button>
        </div>
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-muted-foreground">Loading ticket details...</p>
        </div>
      </div>
    )
  }

  if (error || !ticket) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate('/tickets')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tickets
          </Button>
        </div>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error ? 'Failed to load ticket details.' : 'Ticket not found.'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  const canManageTicket = user?.role === 'admin' || user?.role === 'technician'
  const canSeeInternalNotes = canManageTicket
  const isTicketOwner = ticket.created_by === user?.id

  // Filter notes based on user role
  const visibleNotes = ticket.notes.filter(note => {
    if (canSeeInternalNotes) return true // Admins and techs see all notes
    return !note.is_internal // Regular users only see public notes
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'resolved':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'closed':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'low':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'high':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
      case 'urgent':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const handleStatusUpdate = async () => {
    if (!newStatus || newStatus === ticket.status) {
      setIsEditingStatus(false)
      return
    }

    try {
      await updateTicket({ 
        id: ticket.id, 
        update: { status: newStatus as any }
      })
      await refetch()
      setIsEditingStatus(false)
      setNewStatus('')
    } catch (error) {
      console.error('Failed to update ticket status:', error)
    }
  }

  const handleAddNote = async () => {
    if (!noteText.trim()) return

    try {
      await addNote({
        ticketId: ticket.id,
        note: {
          body: noteText,
          is_internal: isInternalNote
        }
      })
      await refetch()
      setNoteText('')
      setIsAddingNote(false)
      setIsInternalNote(false)
    } catch (error) {
      console.error('Failed to add note:', error)
    }
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate('/tickets')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tickets
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Ticket #{ticket.id}
            </h1>
            <p className="text-muted-foreground">
              Created {formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}
            </p>
          </div>
        </div>
        
        {canManageTicket && (
          <div className="flex items-center space-x-2">
            {isEditingStatus ? (
              <div className="flex items-center space-x-2">
                <Select value={newStatus} onValueChange={setNewStatus}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
                <Button size="sm" onClick={handleStatusUpdate} disabled={isUpdating}>
                  Save
                </Button>
                <Button size="sm" variant="outline" onClick={() => setIsEditingStatus(false)}>
                  Cancel
                </Button>
              </div>
            ) : (
              <Button size="sm" variant="outline" onClick={() => {
                setNewStatus(ticket.status)
                setIsEditingStatus(true)
              }}>
                <Edit className="w-4 h-4 mr-2" />
                Update Status
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Ticket Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Ticket Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{ticket.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="prose dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{ticket.description}</p>
              </div>
            </CardContent>
          </Card>

          {/* Notes Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center">
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Notes & Updates ({visibleNotes.length})
                </CardTitle>
                {(isTicketOwner || canManageTicket) && (
                  <Button 
                    size="sm" 
                    onClick={() => setIsAddingNote(true)}
                    disabled={isAddingNote}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Note
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Add Note Form */}
              {isAddingNote && (
                <div className="space-y-4 p-4 border rounded-lg bg-muted/50">
                  <div>
                    <Label htmlFor="note">Add Note</Label>
                    <Textarea
                      id="note"
                      value={noteText}
                      onChange={(e) => setNoteText(e.target.value)}
                      placeholder="Enter your note here..."
                      className="mt-1"
                      rows={3}
                    />
                  </div>
                  
                  {canManageTicket && (
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="internal"
                        checked={isInternalNote}
                        onChange={(e) => setIsInternalNote(e.target.checked)}
                        className="rounded"
                      />
                      <Label htmlFor="internal" className="text-sm">
                        Internal note (only visible to technicians and admins)
                      </Label>
                    </div>
                  )}
                  
                  <div className="flex justify-end space-x-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        setIsAddingNote(false)
                        setNoteText('')
                        setIsInternalNote(false)
                      }}
                    >
                      Cancel
                    </Button>
                    <Button 
                      size="sm" 
                      onClick={handleAddNote}
                      disabled={!noteText.trim() || isUpdating}
                    >
                      Add Note
                    </Button>
                  </div>
                </div>
              )}

              {/* Notes List */}
              {visibleNotes.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No notes yet.</p>
                  <p className="text-sm">
                    {isTicketOwner || canManageTicket 
                      ? "Be the first to add a note!" 
                      : "Notes will appear here when added."}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {visibleNotes.map((note) => (
                    <div 
                      key={note.id} 
                      className={`p-4 rounded-lg border ${
                        note.is_internal 
                          ? 'bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-800' 
                          : 'bg-background'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <User className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm font-medium">
                            User #{note.author_id}
                          </span>
                          {note.is_internal && (
                            <Badge variant="secondary" className="text-xs">
                              <Lock className="w-3 h-3 mr-1" />
                              Internal
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(note.created_at), { addSuffix: true })}
                        </span>
                      </div>
                      <div className="prose dark:prose-invert prose-sm max-w-none">
                        <p className="whitespace-pre-wrap m-0">{note.body}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status & Priority */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Status & Priority</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge className={getStatusColor(ticket.status)}>
                  {ticket.status.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Priority</span>
                <Badge className={getPriorityColor(ticket.priority)}>
                  {ticket.priority.toUpperCase()}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Ticket Details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Ticket Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Tag className="w-4 h-4 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Ticket ID</p>
                  <p className="font-medium">#{ticket.id}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <User className="w-4 h-4 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Created by</p>
                  <p className="font-medium">User #{ticket.created_by}</p>
                </div>
              </div>
              
              {ticket.assigned_to && (
                <div className="flex items-center space-x-2">
                  <User className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Assigned to</p>
                    <p className="font-medium">User #{ticket.assigned_to}</p>
                  </div>
                </div>
              )}
              
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Created</p>
                  <p className="font-medium">
                    {new Date(ticket.created_at).toLocaleDateString()} at{' '}
                    {new Date(ticket.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Last updated</p>
                  <p className="font-medium">
                    {new Date(ticket.updated_at).toLocaleDateString()} at{' '}
                    {new Date(ticket.updated_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions (for technicians/admins) */}
          {canManageTicket && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full justify-start"
                  onClick={() => setIsAddingNote(true)}
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Add Note
                </Button>
                
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full justify-start"
                  onClick={() => {
                    setIsInternalNote(true)
                    setIsAddingNote(true)
                  }}
                >
                  <Lock className="w-4 h-4 mr-2" />
                  Add Internal Note
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}