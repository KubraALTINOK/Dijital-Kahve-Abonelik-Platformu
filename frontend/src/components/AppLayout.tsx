import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../auth/useAuth'

export function AppLayout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')

  async function handleSignOut() {
    setError('')
    try {
      await signOut()
      navigate('/login')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Çıkış yapılamadı.')
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <NavLink className="brand" to="/">
          KahveCell
        </NavLink>
        <nav className="main-nav" aria-label="Ana menü">
          <NavLink to="/" end>
            Dükkânlar
          </NavLink>
          <NavLink to="/orders/history">Siparişlerim</NavLink>
          <NavLink to="/subscriptions">Abonelik</NavLink>
        </nav>
        <div className="account-menu">
          <span>{user?.full_name || user?.phone_number}</span>
          <button className="button button-secondary" onClick={handleSignOut}>
            Çıkış
          </button>
        </div>
      </header>
      {error && <p className="notice notice-error">{error}</p>}
      <main className="page-content">
        <Outlet />
      </main>
    </div>
  )
}
