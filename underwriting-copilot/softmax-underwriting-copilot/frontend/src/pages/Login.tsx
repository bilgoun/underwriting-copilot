import { useState, type CSSProperties } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../utils/auth'
import { dashboardApi } from '../api/client'

const pageStyle: CSSProperties = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 50%, #f0f4f8 100%)',
  padding: '2rem',
  position: 'relative',
  overflow: 'hidden',
}

const backgroundAccentStyle: CSSProperties = {
  position: 'absolute',
  width: '800px',
  height: '800px',
  background: 'radial-gradient(circle, rgba(10, 132, 255, 0.08) 0%, transparent 70%)',
  borderRadius: '50%',
  filter: 'blur(80px)',
  top: '-200px',
  right: '-200px',
  pointerEvents: 'none',
}

const cardStyle: CSSProperties = {
  background: 'rgba(255, 255, 255, 0.95)',
  backdropFilter: 'blur(40px) saturate(180%)',
  border: '1px solid rgba(0, 0, 0, 0.06)',
  padding: '3.5rem 3rem',
  borderRadius: '24px',
  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08), 0 0 1px rgba(0, 0, 0, 0.04) inset',
  width: '100%',
  maxWidth: '440px',
  position: 'relative',
}

const logoStyle: CSSProperties = {
  fontSize: '2.5rem',
  fontWeight: '700',
  background: 'linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
  marginBottom: '0.5rem',
  letterSpacing: '-0.03em',
}

const subtitleStyle: CSSProperties = {
  color: 'rgba(0, 0, 0, 0.5)',
  marginBottom: '2.5rem',
  fontSize: '0.95rem',
  lineHeight: '1.6',
}

const labelStyle: CSSProperties = {
  display: 'block',
  marginBottom: '0.6rem',
  color: 'rgba(0, 0, 0, 0.7)',
  fontWeight: '500',
  fontSize: '0.875rem',
  letterSpacing: '0.01em',
}

const inputStyle: CSSProperties = {
  width: '100%',
  padding: '0.875rem 1rem',
  background: 'rgba(0, 0, 0, 0.02)',
  border: '1px solid rgba(0, 0, 0, 0.1)',
  borderRadius: '12px',
  fontSize: '0.95rem',
  color: '#1a1a1a',
  transition: 'all 0.2s ease',
  outline: 'none',
}

const buttonStyle: CSSProperties = {
  width: '100%',
  padding: '1rem',
  background: 'linear-gradient(135deg, #0a84ff 0%, #0066cc 100%)',
  color: 'white',
  border: 'none',
  borderRadius: '12px',
  fontSize: '0.95rem',
  fontWeight: '600',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  boxShadow: '0 8px 24px rgba(10, 132, 255, 0.3)',
  letterSpacing: '0.02em',
}

const buttonDisabledStyle: CSSProperties = {
  ...buttonStyle,
  background: 'rgba(255, 255, 255, 0.1)',
  cursor: 'not-allowed',
  boxShadow: 'none',
}

const errorStyle: CSSProperties = {
  padding: '1rem',
  marginBottom: '1.5rem',
  background: 'rgba(255, 59, 48, 0.08)',
  color: '#d32f2f',
  borderRadius: '12px',
  fontSize: '0.875rem',
  border: '1px solid rgba(255, 59, 48, 0.2)',
}

export default function Login() {
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [role, setRole] = useState<'bank' | 'admin'>('bank')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [focusedInput, setFocusedInput] = useState<string | null>(null)

  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const scope = role === 'admin' ? 'dashboard:admin' : 'dashboard:read'
      const response = await dashboardApi.login(clientId, clientSecret, scope)

      login(response.access_token, role)
      navigate(role === 'admin' ? '/admin' : '/bank')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const getInputStyle = (fieldName: string): CSSProperties => ({
    ...inputStyle,
    borderColor: focusedInput === fieldName ? 'rgba(10, 132, 255, 0.5)' : 'rgba(0, 0, 0, 0.1)',
    background: focusedInput === fieldName ? 'rgba(0, 0, 0, 0.03)' : 'rgba(0, 0, 0, 0.02)',
  })

  return (
    <div style={pageStyle}>
      <div style={backgroundAccentStyle} />
      <div style={cardStyle}>
        <h1 style={logoStyle}>Softmax Underwriting</h1>
        <p style={subtitleStyle}>Sign in to access your dashboard</p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={labelStyle}>Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as 'bank' | 'admin')}
              style={getInputStyle('role')}
              onFocus={() => setFocusedInput('role')}
              onBlur={() => setFocusedInput(null)}
            >
              <option value="bank" style={{ background: '#ffffff', color: '#1a1a1a' }}>
                Bank User
              </option>
              <option value="admin" style={{ background: '#ffffff', color: '#1a1a1a' }}>
                Admin
              </option>
            </select>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={labelStyle}>Client ID</label>
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              onFocus={() => setFocusedInput('clientId')}
              onBlur={() => setFocusedInput(null)}
              required
              style={getInputStyle('clientId')}
              placeholder="Enter your client ID"
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Client Secret</label>
            <input
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              onFocus={() => setFocusedInput('clientSecret')}
              onBlur={() => setFocusedInput(null)}
              required
              style={getInputStyle('clientSecret')}
              placeholder="Enter your client secret"
            />
          </div>

          {error && <div style={errorStyle}>{error}</div>}

          <button type="submit" disabled={loading} style={loading ? buttonDisabledStyle : buttonStyle}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}