import type {
  Order,
  PaymentResult,
  Plan,
  QRPayload,
  Shop,
  ShopDetail,
  Subscription,
  TokenResponse,
  User,
} from './types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

const ACCESS_TOKEN_KEY = 'kahvecell.access_token'
const REFRESH_TOKEN_KEY = 'kahvecell.refresh_token'
const USER_KEY = 'kahvecell.user'

export class ApiError extends Error {
  public readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function saveSession(session: TokenResponse): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, session.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, session.refresh_token)
  localStorage.setItem(USER_KEY, JSON.stringify(session.user))
}

export function saveUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function readSessionUser(): User | null {
  const savedUser = localStorage.getItem(USER_KEY)
  if (!savedUser) return null

  try {
    return JSON.parse(savedUser) as User
  } catch (error) {
    if (error instanceof SyntaxError) {
      clearSession()
      return null
    }
    throw error
  }
}

async function responseError(response: Response): Promise<ApiError> {
  let message = `İstek başarısız oldu (${response.status}).`
  try {
    const body: unknown = await response.json()
    if (
      typeof body === 'object' &&
      body !== null &&
      'detail' in body &&
      typeof body.detail === 'string'
    ) {
      message = body.detail
    }
  } catch (error) {
    if (!(error instanceof SyntaxError)) throw error
  }
  return new ApiError(message, response.status)
}

let refreshInProgress: Promise<boolean> | null = null

async function refreshSession(): Promise<boolean> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) return false

  if (!refreshInProgress) {
    refreshInProgress = (async () => {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!response.ok) {
        clearSession()
        return false
      }
      const session = (await response.json()) as TokenResponse
      saveSession(session)
      return true
    })().finally(() => {
      refreshInProgress = null
    })
  }
  return refreshInProgress
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  retryAfterRefresh = true,
): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (accessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  if (response.status === 401 && retryAfterRefresh) {
    if (await refreshSession()) {
      return apiRequest<T>(path, init, false)
    }
  }
  if (!response.ok) throw await responseError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  requestOTP: (phone_number: string) =>
    apiRequest<{ message: string; simulated_otp: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ phone_number }),
    }),
  verifyOTP: (phone_number: string, otp_code: string) =>
    apiRequest<TokenResponse>('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ phone_number, otp_code }),
    }),
  completeProfile: (full_name: string) =>
    apiRequest<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify({ full_name }),
    }),
  logout: (refresh_token: string) =>
    apiRequest<void>('/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token }),
    }),
  shops: (query = '') => apiRequest<Shop[]>(`/shops${query}`),
  shop: (id: number, position?: [number, number]) => {
    const query = position
      ? `?lat=${encodeURIComponent(position[0])}&lng=${encodeURIComponent(position[1])}`
      : ''
    return apiRequest<ShopDetail>(`/shops/${id}${query}`)
  },
  createOrder: (data: {
    shop_id: number
    product_id: number
    size: 'S' | 'M' | 'L'
    sugar: number
    milk_preference: string
    extra_shots: number
  }) =>
    apiRequest<Order>('/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  order: (id: number) => apiRequest<Order>(`/orders/${id}`),
  orderHistory: () => apiRequest<Order[]>('/orders/history'),
  plans: () => apiRequest<Plan[]>('/subscriptions/plans'),
  mySubscription: () => apiRequest<Subscription>('/subscriptions/me'),
  purchasePlan: (subscription_plan: Plan['plan_type'], card_number: string) =>
    apiRequest<PaymentResult>('/subscriptions', {
      method: 'POST',
      body: JSON.stringify({ subscription_plan, card_number }),
    }),
  changePlan: (subscription_plan: Plan['plan_type'], card_number: string) =>
    apiRequest<PaymentResult>('/subscriptions/me', {
      method: 'PATCH',
      body: JSON.stringify({ subscription_plan, card_number }),
    }),
  cancelSubscription: () =>
    apiRequest<Subscription>('/subscriptions/me', { method: 'DELETE' }),
}

export type { QRPayload }
