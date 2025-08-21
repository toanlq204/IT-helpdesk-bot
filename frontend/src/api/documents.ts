import { apiClient } from './client'

export interface Document {
  id: number
  filename: string
  filepath: string
  content_type: string
  size_bytes: number
  uploaded_by: number
  uploaded_at: string
  status: 'pending' | 'parsed' | 'failed'
}

export interface DocumentText {
  id: number
  document_id: number
  text: string
  char_count: number
  created_at: string
}

export interface DocumentWithText extends Document {
  document_text?: DocumentText
}

export const documentsApi = {
  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post('/docs/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getDocuments: async (): Promise<Document[]> => {
    const response = await apiClient.get('/docs/')
    return response.data
  },

  getDocument: async (id: number): Promise<DocumentWithText> => {
    const response = await apiClient.get(`/docs/${id}`)
    return response.data
  },

  deleteDocument: async (id: number): Promise<void> => {
    await apiClient.delete(`/docs/${id}`)
  },

  reparseDocument: async (id: number): Promise<Document> => {
    const response = await apiClient.post(`/docs/${id}/reparse`)
    return response.data
  },

  downloadDocument: async (id: number): Promise<Blob> => {
    const response = await apiClient.get(`/files/${id}`, {
      responseType: 'blob',
    })
    return response.data
  },
}
