import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { DocumentUpload } from '../components/DocumentUpload'
import { DocumentCard } from '../components/DocumentCard'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { useDocuments } from '../hooks/useDocuments'
import { useAuth } from '../hooks/useAuth'
import { Alert, AlertDescription } from '../components/ui/alert'

export const DocumentsPage = () => {
  const { user } = useAuth()
  const { documents, isLoading, error } = useDocuments()

  // Only admins can access this page
  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>
            Access denied. Only administrators can manage documents.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>
            Failed to load documents. Please try again.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Documents</h1>
              <p className="text-muted-foreground">Manage knowledge base documents</p>
            </div>
            <DocumentUpload />
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">

      <Card>
        <CardHeader>
          <CardTitle>Document Library ({documents.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="mb-2">No documents uploaded yet.</p>
              <p className="text-sm">Upload your first document to get started with the knowledge base.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((document) => (
                <DocumentCard key={document.id} document={document} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </div>
  )
}
