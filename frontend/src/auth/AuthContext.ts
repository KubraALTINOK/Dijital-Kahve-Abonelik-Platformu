import { createContext } from 'react'
import type { User } from '../api/types'

export interface AuthContextValue {
  user: User | null
  signIn: (phone: string, otp: string) => Promise<User>
  completeProfile: (fullName: string) => Promise<User>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
