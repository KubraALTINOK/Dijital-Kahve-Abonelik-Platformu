import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { ShopDetail, Subscription } from '../api/types'

export function NewOrderPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const shopId = Number(searchParams.get('shop_id'))
  const requestedProductId = searchParams.get('product_id') ?? ''
  const [result, setResult] = useState<{
    id: number
    shop?: ShopDetail
    error?: string
  } | null>(null)
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [subscriptionLoading, setSubscriptionLoading] = useState(true)
  const [subscriptionError, setSubscriptionError] = useState('')
  const [subscriptionCheckedAt, setSubscriptionCheckedAt] = useState<number | null>(
    null,
  )
  const [productId, setProductId] = useState('')
  const [size, setSize] = useState<'S' | 'M' | 'L'>('M')
  const [sugar, setSugar] = useState(0)
  const [milk, setMilk] = useState('Normal')
  const [extraShots, setExtraShots] = useState(0)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!Number.isInteger(shopId) || shopId < 1) return
    let active = true
    api
      .shop(shopId)
      .then((shop) => {
        if (active) {
          setResult({ id: shopId, shop })
          const requestedProduct = shop.menu.find(
            (product) => product.id === Number(requestedProductId),
          )
          setProductId(String(requestedProduct?.id ?? shop.menu[0]?.id ?? ''))
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setResult({
            id: shopId,
            error:
              reason instanceof ApiError
                ? reason.message
                : 'Dükkân yüklenemedi.',
          })
        }
      })
    return () => {
      active = false
    }
  }, [shopId, requestedProductId])

  useEffect(() => {
    let active = true
    api
      .mySubscription()
      .then((currentSubscription) => {
        if (active) {
          setSubscription(currentSubscription)
          setSubscriptionCheckedAt(Date.now())
        }
      })
      .catch((reason: unknown) => {
        if (!active) return
        if (reason instanceof ApiError && reason.status === 404) {
          setSubscription(null)
          setSubscriptionCheckedAt(Date.now())
        } else {
          setSubscriptionError(
            reason instanceof ApiError
              ? reason.message
              : 'Abonelik bilgisi yüklenemedi.',
          )
        }
      })
      .finally(() => {
        if (active) setSubscriptionLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const page = result?.id === shopId ? result : null
  const shop = page?.shop ?? null
  const selectedProduct = shop?.menu.find(
    (product) => product.id === Number(productId),
  )
  const expiresAt = subscription?.expires_at
    ? Date.parse(subscription.expires_at)
    : null
  const subscriptionExpired =
    expiresAt !== null &&
    subscriptionCheckedAt !== null &&
    (!Number.isFinite(expiresAt) || expiresAt <= subscriptionCheckedAt)
  const hasActiveSubscription =
    subscription?.status === 'ACTIVE' && !subscriptionExpired
  const isUnlimited =
    subscription?.plan_type === 'UNLIMITED' &&
    subscription.remaining_credits === -1
  const hasCredits =
    isUnlimited || (subscription !== null && subscription.remaining_credits > 0)
  const remainingCredits = subscription?.remaining_credits ?? 0
  const canOrder =
    !subscriptionLoading &&
    !subscriptionError &&
    hasActiveSubscription &&
    hasCredits

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canOrder) return
    if (!shop || !selectedProduct) {
      setError('Sipariş için geçerli bir ürün seçin.')
      return
    }

    setWorking(true)
    setError('')
    try {
      const order = await api.createOrder({
        shop_id: shop.id,
        product_id: selectedProduct.id,
        size,
        sugar,
        milk_preference: milk,
        extra_shots: extraShots,
      })
      navigate(`/orders/${order.id}/qr`)
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : 'Sipariş oluşturulamadı.',
      )
    } finally {
      setWorking(false)
    }
  }

  if (!Number.isInteger(shopId) || shopId < 1) {
    return (
      <p className="notice notice-error">
        Sipariş vermek için önce bir dükkân seçin.
      </p>
    )
  }
  if (page?.error) return <p className="notice notice-error">{page.error}</p>
  if (!shop) return <p>Menü yükleniyor…</p>

  return (
    <section className="page-stack narrow-page">
      <Link to={`/shops/${shop.id}`}>← {shop.name} menüsüne dön</Link>
      <div>
        <p className="eyebrow">Yeni sipariş</p>
        <h1>Kahveni özelleştir</h1>
      </div>
      {selectedProduct && (
        <section className="panel selected-product">
          <div>
            <p className="eyebrow">Seçilen ürün</p>
            <h2>{selectedProduct.name}</h2>
            {selectedProduct.description && <p>{selectedProduct.description}</p>}
          </div>
          <strong>{Number(selectedProduct.price).toFixed(2)} TL</strong>
        </section>
      )}
      <section className="panel credit-panel" aria-live="polite">
        {subscriptionLoading ? (
          <p>Abonelik ve kahve hakkı kontrol ediliyor…</p>
        ) : subscriptionError ? (
          <p className="notice notice-error">{subscriptionError}</p>
        ) : !hasActiveSubscription ? (
          <div>
            <p>
              {subscriptionExpired
                ? 'Aboneliğinizin süresi dolmuş.'
                : 'Sipariş verebilmek için aktif bir aboneliğiniz olmalı.'}
            </p>
            <Link className="button" to="/subscriptions">
              Abonelik sayfasına git
            </Link>
          </div>
        ) : !hasCredits ? (
          <div>
            <p>Kahve hakkınız bitmiş. Sipariş vermek için paketinizi yenileyin.</p>
            <Link className="button" to="/subscriptions">
              Abonelik sayfasına git
            </Link>
          </div>
        ) : isUnlimited ? (
          <>
            <strong>Unlimited aboneliğiniz aktif.</strong>
            <p>Bu siparişte kredi düşülmez; kahve hakkınız sınırsızdır.</p>
          </>
        ) : (
          <>
            <strong>Kalan kahve krediniz: {subscription?.remaining_credits}</strong>
            <p>
              Bu sipariş sonrası {Math.max(remainingCredits - 1, 0)} kredi kalacak.
            </p>
          </>
        )}
      </section>
      <form className="panel form-stack" onSubmit={handleSubmit}>
        <label>
          Ürün
          <select
            required
            value={productId}
            onChange={(event) => setProductId(event.target.value)}
            disabled={shop.menu.length === 0}
          >
            {shop.menu.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} · {Number(product.price).toFixed(2)} TL
              </option>
            ))}
          </select>
        </label>
        <label>
          Boyut
          <select
            value={size}
            onChange={(event) => setSize(event.target.value as 'S' | 'M' | 'L')}
          >
            <option value="S">Small (S)</option>
            <option value="M">Medium (M)</option>
            <option value="L">Large (L)</option>
          </select>
        </label>
        <label>
          Şeker (0–5)
          <input
            type="number"
            min={0}
            max={5}
            value={sugar}
            onChange={(event) => setSugar(Number(event.target.value))}
          />
        </label>
        <label>
          Süt tipi
          <select value={milk} onChange={(event) => setMilk(event.target.value)}>
            <option>Normal</option>
            <option>Yağsız</option>
            <option>Yulaf</option>
            <option>Badem</option>
            <option>Sütsüz</option>
          </select>
        </label>
        <label>
          Ek shot (0–3)
          <input
            type="number"
            min={0}
            max={3}
            value={extraShots}
            onChange={(event) => setExtraShots(Number(event.target.value))}
          />
        </label>
        {error && <p className="notice notice-error">{error}</p>}
        <button
          className="button"
          disabled={
            working ||
            subscriptionLoading ||
            Boolean(subscriptionError) ||
            !canOrder ||
            !selectedProduct
          }
        >
          {working ? 'Sipariş veriliyor…' : 'Siparişi Onayla'}
        </button>
      </form>
    </section>
  )
}
