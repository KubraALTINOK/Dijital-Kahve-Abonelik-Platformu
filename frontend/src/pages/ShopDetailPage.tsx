import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { Product, ShopDetail } from '../api/types'

const DEFAULT_LOCATION: [number, number] = [39.9206, 32.8541]

const MENU_CATEGORIES = [
  { key: 'espresso', label: 'Espresso Bazlı' },
  { key: 'filter', label: 'Filtre Kahveler' },
  { key: 'cold', label: 'Soğuk İçecekler' },
  { key: 'other', label: 'Diğer' },
] as const

type MenuCategory = (typeof MENU_CATEGORIES)[number]['key']

function categoryForProduct(product: Product): MenuCategory {
  const category = product.category.trim().toLocaleLowerCase('tr-TR')
    .replace(/[\s-]+/g, '_')
  const categoryAliases: Record<string, MenuCategory> = {
    espresso: 'espresso',
    espresso_based: 'espresso',
    espresso_bazli: 'espresso',
    filter: 'filter',
    filter_coffee: 'filter',
    filtre: 'filter',
    filtre_kahveler: 'filter',
    cold: 'cold',
    cold_drink: 'cold',
    cold_drinks: 'cold',
    iced: 'cold',
    soguk_icecekler: 'cold',
    other: 'other',
    other_drinks: 'other',
    diger: 'other',
  }
  const explicitCategory = categoryAliases[category]
  if (explicitCategory) return explicitCategory

  const name = product.name.toLocaleLowerCase('tr-TR')
  if (name.includes('filtre') || name.includes('filter')) return 'filter'
  if (
    name.includes('soğuk') ||
    name.includes('soguk') ||
    name.includes('cold') ||
    name.includes('iced') ||
    name.includes('frappe')
  ) {
    return 'cold'
  }
  if (
    ['espresso', 'americano', 'cappuccino', 'latte', 'macchiato', 'mocha'].some(
      (keyword) => name.includes(keyword),
    )
  ) {
    return 'espresso'
  }
  return 'other'
}

export function ShopDetailPage() {
  const { shopId } = useParams()
  const location = useLocation()
  const routeState = location.state as { position?: [number, number] } | null
  const position = routeState?.position ?? DEFAULT_LOCATION
  const id = Number(shopId)
  const [result, setResult] = useState<{
    id: number
    shop?: ShopDetail
    error?: string
  } | null>(null)

  useEffect(() => {
    if (!Number.isInteger(id) || id < 1) {
      return
    }
    let active = true
    api
      .shop(id, position)
      .then((result) => {
        if (active) setResult({ id, shop: result })
      })
      .catch((reason: unknown) => {
        if (active) {
          setResult({
            id,
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
  }, [id, position])

  if (!Number.isInteger(id) || id < 1) {
    return <p className="notice notice-error">Dükkân numarası geçersiz.</p>
  }
  const page = result?.id === id ? result : null
  if (page?.error) return <p className="notice notice-error">{page.error}</p>
  const shop = page?.shop
  if (!shop) return <p>Menü yükleniyor…</p>
  const productsByCategory = new Map<MenuCategory, Product[]>(
    MENU_CATEGORIES.map(({ key }) => [
      key,
      shop.menu.filter((product) => categoryForProduct(product) === key),
    ]),
  )

  return (
    <section className="page-stack shop-detail-page">
      <Link to="/">← Dükkânlara dön</Link>
      <header className="panel shop-detail-header">
        <div className="shop-detail-heading">
          <p className="eyebrow">Dükkân detayı</p>
          <h1>{shop.name}</h1>
          <p>{shop.address}</p>
          <div className="shop-facts">
            <span>
              <strong>Çalışma saatleri:</strong>{' '}
              {shop.working_hours || 'Bilgi eklenmemiş'}
            </span>
            <span>
              <strong>Puan:</strong> {shop.rating.toFixed(1)}
            </span>
            <span>
              <strong>Mesafe:</strong>{' '}
              {shop.distance_km === null
                ? 'Hesaplanamadı'
                : `${shop.distance_km.toFixed(2)} km`}
            </span>
          </div>
        </div>
      </header>
      <section className="menu-section">
        <div>
          <p className="eyebrow">Menü</p>
          <h2>İçeceğini seç</h2>
        </div>
        {shop.menu.length === 0 ? (
          <p className="empty-state">Bu dükkânın menüsü henüz eklenmemiş.</p>
        ) : (
          MENU_CATEGORIES.map(({ key, label }) => (
            <section className="menu-category" key={key}>
              <h3>{label}</h3>
              {productsByCategory.get(key)?.length ? (
                <div className="menu-product-list">
                  {productsByCategory.get(key)?.map((product) => (
                    <article className="panel menu-product" key={product.id}>
                      <div>
                        <h4>{product.name}</h4>
                        {product.description && <p>{product.description}</p>}
                      </div>
                      <div className="menu-product-actions">
                        <strong>{Number(product.price).toFixed(2)} TL</strong>
                        <Link
                          className="button"
                          to={`/orders/new?shop_id=${shop.id}&product_id=${product.id}`}
                        >
                          Sipariş Ver
                        </Link>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="empty-category">Bu kategoride ürün bulunmuyor.</p>
              )}
            </section>
          ))
        )}
      </section>
    </section>
  )
}
