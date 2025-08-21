import { apiClient } from './client'

export interface User {
  id: number
  email: string
  role: string
}

export interface Ticket {
  id: number
  created_by: number
  creator?: User
  assigned_to?: number
  assignee?: User
  title: string
  description: string
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high'
  created_at: string
  updated_at: string
  notes: TicketNote[]
}

export interface TicketNote {
  id: number
  ticket_id: number
  author_id: number
  author?: User
  body: string
  is_internal: boolean
  created_at: string
}

export interface CreateTicketRequest {
  title: string
  description: string
  priority: 'low' | 'medium' | 'high'
}

export interface UpdateTicketRequest {
  title?: string
  description?: string
  status?: 'open' | 'in_progress' | 'resolved' | 'closed'
  priority?: 'low' | 'medium' | 'high'
  assigned_to?: number
}

export interface CreateNoteRequest {
  body: string
  is_internal: boolean
}

export const ticketsApi = {
  createTicket: async (ticket: CreateTicketRequest): Promise<Ticket> => {
    const response = await apiClient.post('/tickets/', ticket)
    return response.data
  },

  getTickets: async (): Promise<Ticket[]> => {
    const response = await apiClient.get('/tickets/')
    return response.data
  },

  getUnassignedTickets: async (): Promise<Ticket[]> => {
    const response = await apiClient.get('/tickets/unassigned')
    return response.data
  },

  getAssignedTickets: async (): Promise<Ticket[]> => {
    const response = await apiClient.get('/tickets/assigned')
    return response.data
  },

  getTicket: async (id: number): Promise<Ticket> => {
    const response = await apiClient.get(`/tickets/${id}`)
    return response.data
  },

  updateTicket: async (id: number, update: UpdateTicketRequest): Promise<Ticket> => {
    const response = await apiClient.patch(`/tickets/${id}`, update)
    return response.data
  },

  addNote: async (ticketId: number, note: CreateNoteRequest): Promise<TicketNote> => {
    const response = await apiClient.post(`/tickets/${ticketId}/notes`, note)
    return response.data
  },

  getTechnicians: async (): Promise<User[]> => {
    const response = await apiClient.get('/tickets/technicians')
    return response.data
  },

  assignTicket: async (ticketId: number, userId: number): Promise<Ticket> => {
    const response = await apiClient.post(`/tickets/${ticketId}/assign/${userId}`)
    return response.data
  },

  unassignTicket: async (ticketId: number): Promise<Ticket> => {
    const response = await apiClient.post(`/tickets/${ticketId}/unassign`)
    return response.data
  },
}
