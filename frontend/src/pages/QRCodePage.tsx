import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { Order } from '../api/types'
import { ORDER_STATUS_LABELS, orderStatusClass } from '../utils/orderStatus'

const STATUS_POLL_INTERVAL_MS = 3_000

function statusDescription(status: Order['status']): string {
  switch (status) {
    case 'PENDING':
      return 'Dükkân siparişinizi bekliyor.'
    case 'ACCEPTED':
      return 'Dükkân siparişinizi kabul etti.'
    case 'PREPARING':
      return 'Kahveniz hazırlanıyor.'
    case 'READY':
      return 'Siparişiniz hazır; QR kodunu dükkânda gösterin.'
    case 'DELIVERED':
      return 'Siparişiniz teslim edildi.'
  }
}

export function QRCodePage() {
  const { orderId } = useParams()
  const id = Number(orderId)
  const [result, setResult] = useState<{ id: number; order: Order } | null>(null)
  const [pollingError, setPollingError] = useState<{
    id: number
    message: string
  } | null>(null)

  useEffect(() => {
    if (!Number.isInteger(id) || id < 1) return
    let active = true
    let timer: number | undefined

    async function refreshOrder() {
      let delivered = false
      try {
        const updatedOrder = await api.order(id)
        if (active) {
          setResult({ id, order: updatedOrder })
          setPollingError(null)
        }
        delivered = updatedOrder.status === 'DELIVERED'
      } catch (reason) {
        if (active) {
          setPollingError({
            id,
            message:
              reason instanceof ApiError
                ? reason.message
                : 'Sipariş durumu alınamadı; yeniden deneniyor.',
          })
        }
      }

      if (active && !delivered) {
        timer = window.setTimeout(
          refreshOrder,
          STATUS_POLL_INTERVAL_MS,
        )
      }
    }

    void refreshOrder()
    return () => {
      active = false
      if (timer !== undefined) window.clearTimeout(timer)
    }
  }, [id])

  if (!Number.isInteger(id) || id < 1) {
    return <p className="notice notice-error">Sipariş numarası geçersiz.</p>
  }
  const order = result?.id === id ? result.order : null
  const error = pollingError?.id === id ? pollingError.message : ''
  if (!order) {
    return error ? (
      <p className="notice notice-error">{error}</p>
    ) : (
      <p>Sipariş ve QR kodu yükleniyor…</p>
    )
  }

  return (
    <section className="page-stack narrow-page qr-page">
      <Link to="/orders/history">← Siparişlerime dön</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Sipariş #{order.id}</p>
          <h1>Siparişini takip et</h1>
          <p>
            {order.product.name} · {order.shop.name} · {order.size}
          </p>
        </div>
      </div>
      {error && <p className="notice notice-error">{error}</p>}
      {order.status === 'DELIVERED' ? (
        <section className="panel order-delivered">
          <span className="success-check" aria-hidden="true">
            ✓
          </span>
          <p className={`order-status ${orderStatusClass(order.status)}`}>
            {ORDER_STATUS_LABELS[order.status]}
          </p>
          <h2>Afiyet olsun!</h2>
          <p>{statusDescription(order.status)}</p>
          <Link className="button" to="/orders/history">
            Sipariş geçmişime dön
          </Link>
        </section>
      ) : (
        <>
          <div className="panel qr-panel">
            <img src={order.qr_code_data_url} alt="Sipariş teslim alma QR kodu" />
            <p
              key={order.status}
              className={`order-status ${orderStatusClass(order.status)}`}
              aria-live="polite"
            >
              {ORDER_STATUS_LABELS[order.status]}
            </p>
            <p>{statusDescription(order.status)}</p>
          </div>
          <details className="panel">
            <summary>İmzalı QR verisini göster</summary>
            <pre className="json-block">
              {JSON.stringify(order.qr_payload, null, 2)}
            </pre>
          </details>
        </>
      )}
    </section>
  )
}
