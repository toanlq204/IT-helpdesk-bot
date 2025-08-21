import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ticketsApi, Ticket, CreateTicketRequest, UpdateTicketRequest, CreateNoteRequest } from '../api/tickets'

export const useTickets = () => {
  const queryClient = useQueryClient()

  const ticketsQuery = useQuery({
    queryKey: ['tickets'],
    queryFn: ticketsApi.getTickets,
  })

  const unassignedTicketsQuery = useQuery({
    queryKey: ['tickets', 'unassigned'],
    queryFn: ticketsApi.getUnassignedTickets,
  })

  const assignedTicketsQuery = useQuery({
    queryKey: ['tickets', 'assigned'],
    queryFn: ticketsApi.getAssignedTickets,
  })

  const createTicketMutation = useMutation({
    mutationFn: ticketsApi.createTicket,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
    },
  })

  const updateTicketMutation = useMutation({
    mutationFn: ({ id, update }: { id: number; update: UpdateTicketRequest }) =>
      ticketsApi.updateTicket(id, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
    },
  })

  const addNoteMutation = useMutation({
    mutationFn: ({ ticketId, note }: { ticketId: number; note: CreateNoteRequest }) =>
      ticketsApi.addNote(ticketId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
    },
  })

  return {
    tickets: ticketsQuery.data || [],
    unassignedTickets: unassignedTicketsQuery.data || [],
    assignedTickets: assignedTicketsQuery.data || [],
    isLoading: ticketsQuery.isLoading,
    error: ticketsQuery.error,
    createTicket: createTicketMutation.mutateAsync,
    updateTicket: updateTicketMutation.mutateAsync,
    addNote: addNoteMutation.mutateAsync,
    isCreating: createTicketMutation.isPending,
    isUpdating: updateTicketMutation.isPending,
  }
}

export const useTicket = (id: number) => {
  const queryClient = useQueryClient()

  const ticketQuery = useQuery({
    queryKey: ['tickets', id],
    queryFn: () => ticketsApi.getTicket(id),
    enabled: !!id,
  })

  return {
    ticket: ticketQuery.data,
    isLoading: ticketQuery.isLoading,
    error: ticketQuery.error,
    refetch: ticketQuery.refetch,
  }
}
