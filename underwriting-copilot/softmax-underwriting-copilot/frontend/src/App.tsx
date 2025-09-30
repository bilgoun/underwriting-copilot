import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import BankDashboard from './pages/BankDashboard'
import AdminDashboard from './pages/AdminDashboard'
import { useAuth } from './utils/auth'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/bank/*"
        element={
          <ProtectedRoute role="bank">
            <BankDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute role="admin">
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

function ProtectedRoute({ children, role }: { children: React.ReactNode; role: string }) {
  const { isAuthenticated, userRole } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (userRole !== role) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default App