import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, LoginRequest } from '../api/auth'
import { useAuthStore } from '../store/auth'

export const useAuth = () => {
  const { user, isAuthenticated, login, logout } = useAuthStore()
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    mutationFn: authApi.login,
  })

  const hasToken = !!localStorage.getItem('access_token')
  
  const getCurrentUserQuery = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: hasToken && !user,
    retry: false,
  })

  // Handle user data when query succeeds
  if (getCurrentUserQuery.data && !user) {
    const token = localStorage.getItem('access_token')
    if (token) {
      login(getCurrentUserQuery.data, token)
    }
  }

  // Handle auth errors
  if (getCurrentUserQuery.error) {
    logout()
  }

  // If no token and no user, we're not authenticated
  const shouldShowLoading = hasToken && getCurrentUserQuery.isLoading && !user

  const handleLogin = async (credentials: LoginRequest) => {
    try {
      const response = await loginMutation.mutateAsync(credentials)
      localStorage.setItem('access_token', response.access_token)
      
      // Fetch user data after setting token
      const userData = await authApi.getCurrentUser()
      login(userData, response.access_token)
      
      return { success: true }
    } catch (error: any) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      }
    }
  }

  const handleLogout = () => {
    logout()
    queryClient.clear()
  }

  return {
    user,
    isAuthenticated: isAuthenticated || !!user,
    login: handleLogin,
    logout: handleLogout,
    isLoading: shouldShowLoading,
    error: loginMutation.error || getCurrentUserQuery.error,
  }
}
