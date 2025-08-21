import { Card, CardContent, CardHeader } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Document } from '../api/documents'
import { useDocuments } from '../hooks/useDocuments'
import { formatDistanceToNow } from 'date-fns'
import { 
  FileText, 
  Download, 
  Trash2, 
  RefreshCw, 
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react'

interface DocumentCardProps {
  document: Document
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'parsed':
      return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'failed':
      return <AlertCircle className="w-4 h-4 text-red-500" />
    case 'pending':
      return <Clock className="w-4 h-4 text-yellow-500" />
    default:
      return <Clock className="w-4 h-4 text-gray-500" />
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'parsed':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'failed':
      return 'bg-red-100 text-red-800 border-red-200'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export const DocumentCard = ({ document }: DocumentCardProps) => {
  const { deleteDocument, reparseDocument, isDeleting, isReparsing } = useDocuments()

  const handleDownload = async () => {
    try {
      const { documentsApi } = await import('../api/documents')
      const blob = await documentsApi.downloadDocument(document.id)
      const url = window.URL.createObjectURL(blob)
      const link = window.document.createElement('a')
      link.href = url
      link.download = document.filename
      window.document.body.appendChild(link)
      link.click()
      window.document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete "${document.filename}"?`)) {
      try {
        await deleteDocument(document.id)
      } catch (error) {
        console.error('Delete failed:', error)
      }
    }
  }

  const handleReparse = async () => {
    try {
      await reparseDocument(document.id)
    } catch (error) {
      console.error('Reparse failed:', error)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <FileText className="w-8 h-8 text-blue-500 mt-1" />
            <div className="space-y-1">
              <h3 className="font-semibold text-lg">{document.filename}</h3>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span>{formatFileSize(document.size_bytes)}</span>
                <span>•</span>
                <span>{document.content_type}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusIcon(document.status)}
            <Badge className={getStatusColor(document.status)}>
              {document.status}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            Uploaded {formatDistanceToNow(new Date(document.uploaded_at), { addSuffix: true })}
          </span>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4" />
            </Button>
            {document.status === 'failed' && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleReparse}
                disabled={isReparsing}
              >
                <RefreshCw className={`w-4 h-4 ${isReparsing ? 'animate-spin' : ''}`} />
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
