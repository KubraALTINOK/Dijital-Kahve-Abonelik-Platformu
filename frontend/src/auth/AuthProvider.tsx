import { useMemo, useState, type ReactNode } from 'react'
import { api, clearSession, readSessionUser, saveSession, saveUser } from '../api/client'
import { AuthContext, type AuthContextValue } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState(readSessionUser)

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      signIn: async (phone, otp) => {
        const session = await api.verifyOTP(phone, otp)
        saveSession(session)
        setUser(session.user)
        return session.user
      },
      completeProfile: async (fullName) => {
        const updatedUser = await api.completeProfile(fullName)
        saveUser(updatedUser)
        setUser(updatedUser)
        return updatedUser
      },
      signOut: async () => {
        const refreshToken = localStorage.getItem('kahvecell.refresh_token')
        try {
          if (refreshToken) await api.logout(refreshToken)
        } finally {
          clearSession()
          setUser(null)
        }
      },
    }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
