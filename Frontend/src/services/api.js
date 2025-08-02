import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// File upload service
export const fileService = {
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Conversation service
export const conversationService = {
  getConversations: async () => {
    const response = await api.get('/conversations');
    return response.data;
  },

  getMessages: async (conversationId) => {
    const response = await api.get(`/conversations/${conversationId}/messages`);
    return response.data;
  },

  sendMessage: async (message, conversationId = null, fileIds = []) => {
    const response = await api.post('/chat', {
      message,
      conversation_id: conversationId,
      file_ids: fileIds,
    });
    return response.data;
  },
};

// Ticket service
export const ticketService = {
  getTickets: async () => {
    const response = await api.get('/tickets');
    return response.data;
  },

  createTicket: async (ticket) => {
    const response = await api.post('/tickets', ticket);
    return response.data;
  },

  updateTicket: async (ticketId, updates) => {
    const response = await api.put(`/tickets/${ticketId}`, updates);
    return response.data;
  },

  deleteTicket: async (ticketId) => {
    const response = await api.delete(`/tickets/${ticketId}`);
    return response.data;
  },

  getTicket: async (ticketId) => {
    const response = await api.get(`/tickets/${ticketId}`);
    return response.data;
  },
}; 