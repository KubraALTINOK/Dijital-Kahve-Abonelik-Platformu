import type { Order } from '../api/types'

export const ORDER_STATUS_LABELS: Record<Order['status'], string> = {
  PENDING: 'Bekliyor',
  ACCEPTED: 'Kabul Edildi',
  PREPARING: 'Hazırlanıyor',
  READY: 'Hazır',
  DELIVERED: 'Teslim Edildi',
}

export function orderStatusClass(status: Order['status']): string {
  return `status-${status.toLowerCase()}`
}
