import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, Document } from '../api/documents'

export const useDocuments = () => {
  const queryClient = useQueryClient()

  const documentsQuery = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.getDocuments,
  })

  const uploadDocumentMutation = useMutation({
    mutationFn: documentsApi.uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const deleteDocumentMutation = useMutation({
    mutationFn: documentsApi.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const reparseDocumentMutation = useMutation({
    mutationFn: documentsApi.reparseDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  return {
    documents: documentsQuery.data || [],
    isLoading: documentsQuery.isLoading,
    error: documentsQuery.error,
    uploadDocument: uploadDocumentMutation.mutateAsync,
    deleteDocument: deleteDocumentMutation.mutateAsync,
    reparseDocument: reparseDocumentMutation.mutateAsync,
    isUploading: uploadDocumentMutation.isPending,
    isDeleting: deleteDocumentMutation.isPending,
    isReparsing: reparseDocumentMutation.isPending,
  }
}

export const useDocument = (id: number) => {
  const documentQuery = useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentsApi.getDocument(id),
    enabled: !!id,
  })

  return {
    document: documentQuery.data,
    isLoading: documentQuery.isLoading,
    error: documentQuery.error,
  }
}
