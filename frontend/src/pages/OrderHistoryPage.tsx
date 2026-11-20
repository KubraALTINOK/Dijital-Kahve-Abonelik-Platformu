import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { Order } from '../api/types'
import { ORDER_STATUS_LABELS, orderStatusClass } from '../utils/orderStatus'

function formatOrderDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('tr-TR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function OrderHistoryPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api
      .orderHistory()
      .then((result) => {
        if (active) setOrders(result)
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(
            reason instanceof ApiError
              ? reason.message
              : 'Sipariş geçmişi yüklenemedi.',
          )
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const newestFirst = [...orders].sort(
    (first, second) =>
      Date.parse(second.created_at) - Date.parse(first.created_at) ||
      second.id - first.id,
  )

  return (
    <section className="page-stack order-history-page">
      <div>
        <p className="eyebrow">Hesabım</p>
        <h1>Sipariş geçmişim</h1>
      </div>
      {error ? (
        <p className="notice notice-error">{error}</p>
      ) : loading ? (
        <p>Siparişler yükleniyor…</p>
      ) : newestFirst.length === 0 ? (
        <p className="empty-state">Henüz siparişin yok.</p>
      ) : (
        <div className="panel order-history-list">
          {newestFirst.map((order) => (
            <article className="order-history-row" key={order.id}>
              <time dateTime={order.created_at}>
                {formatOrderDate(order.created_at)}
              </time>
              <div>
                <strong>{order.shop.name}</strong>
                <p>{order.product.name}</p>
              </div>
              <span
                className={`order-status ${orderStatusClass(order.status)}`}
              >
                {ORDER_STATUS_LABELS[order.status]}
              </span>
              <Link to={`/orders/${order.id}/qr`}>Detay / QR</Link>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
