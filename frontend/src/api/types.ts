export interface User {
  id: number
  phone_number: string
  full_name: string
  role: 'CUSTOMER' | 'SHOP_OWNER' | 'ADMIN'
  profile_complete: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  user: User
}

export interface Shop {
  id: number
  name: string
  address: string
  latitude: number
  longitude: number
  working_hours: string | null
  rating: number
  distance_km: number | null
}

export interface Product {
  id: number
  name: string
  description: string | null
  price: string
  category: string
}

export interface ShopDetail extends Shop {
  menu: Product[]
}

export interface QRPayload {
  order_id: string
  user_id: string
  shop_id: string
  created_at: string
  signature: string
}

export interface Order {
  id: number
  user_id: number
  shop_id: number
  product_id: number
  status: 'PENDING' | 'ACCEPTED' | 'PREPARING' | 'READY' | 'DELIVERED'
  size: 'S' | 'M' | 'L'
  sugar: number
  milk_preference: string | null
  extra_shots: number
  created_at: string
  shop: Shop
  product: Product
  qr_payload: QRPayload
  qr_code_data_url: string
}

export interface Plan {
  plan_type: 'STARTER' | 'PREMIUM' | 'UNLIMITED'
  name: string
  monthly_price: string
  coffee_credits: number | null
  guest_passes: number
  priority_service: boolean
}

export interface Subscription {
  id: number
  plan_type: Plan['plan_type']
  remaining_credits: number
  status: 'ACTIVE' | 'PAUSED' | 'CANCELLED'
  started_at: string
  expires_at: string | null
}

export interface PaymentResult {
  success: boolean
  transaction_id: string
  amount: string
  message: string
  subscription: Subscription | null
}
