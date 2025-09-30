import { useState } from 'react'

interface AuthState {
  isAuthenticated: boolean
  userRole: string | null
  token: string | null
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>(() => {
    const token = localStorage.getItem('token')
    const role = localStorage.getItem('role')
    return {
      isAuthenticated: !!token,
      userRole: role,
      token,
    }
  })

  const login = (token: string, role: string) => {
    localStorage.setItem('token', token)
    localStorage.setItem('role', role)
    setAuthState({ isAuthenticated: true, userRole: role, token })
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    setAuthState({ isAuthenticated: false, userRole: null, token: null })
  }

  return {
    ...authState,
    login,
    logout,
  }
}