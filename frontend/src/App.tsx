import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { ChatPage } from './pages/ChatPage'
import { TicketsPage } from './pages/TicketsPage'
import { TicketDetailPage } from './pages/TicketDetailPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { LoadingSpinner } from './components/LoadingSpinner'
import { useEffect } from 'react'

function App() {
  // Apply dark theme by default
  useEffect(() => {
    document.documentElement.classList.add('dark')
  }, [])
  const { isAuthenticated, isLoading, user } = useAuth()

  // Show loading only if we're actually checking authentication
  if (isLoading && !user) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/tickets" element={<TicketsPage />} />
        <Route path="/tickets/:id" element={<TicketDetailPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/login" element={<Navigate to="/chat" replace />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </Layout>
  )
}

export default App
