import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { Shop } from '../api/types'
import { ShopMap } from '../components/ShopMap'

const ANKARA_CENTER: [number, number] = [39.9206, 32.8541]
const DEFAULT_LOCATION_LABEL = 'Varsayılan konum: Ankara Kızılay'

export function HomePage() {
  const geolocationAvailable =
    typeof navigator !== 'undefined' && Boolean(navigator.geolocation)
  const [shops, setShops] = useState<Shop[]>([])
  const [search, setSearch] = useState('')
  const [position, setPosition] = useState<[number, number]>(ANKARA_CENTER)
  const [locationLabel, setLocationLabel] = useState(DEFAULT_LOCATION_LABEL)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [locationNotice, setLocationNotice] = useState(
    geolocationAvailable
      ? ''
      : 'Konum özelliği kullanılamıyor; Ankara Kızılay varsayılan konum olarak kullanılıyor.',
  )

  useEffect(() => {
    let active = true
    if (!navigator.geolocation) return

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        if (active) {
          setLoading(true)
          setError('')
          setPosition([coords.latitude, coords.longitude])
          setLocationLabel('Konumunuz')
          setLocationNotice('')
        }
      },
      () => {
        if (active) {
          setPosition(ANKARA_CENTER)
          setLocationLabel(DEFAULT_LOCATION_LABEL)
          setLocationNotice(
            'Konum izni verilmedi veya konum alınamadı; Ankara Kızılay varsayılan konum olarak kullanılıyor.',
          )
        }
      },
      { timeout: 8000, maximumAge: 60_000 },
    )
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const params = new URLSearchParams()
    params.set('lat', String(position[0]))
    params.set('lng', String(position[1]))
    const query = search.trim()
    if (query) params.set('q', query)
    const suffix = params.size ? `?${params.toString()}` : ''
    let active = true
    api
      .shops(suffix)
      .then((result) => {
        if (active) setShops(result)
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(
            reason instanceof ApiError ? reason.message : 'Dükkânlar yüklenemedi.',
          )
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [position, search])

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div className="home-heading">
          <p className="eyebrow">KahveCell</p>
          <h1>Yakınındaki kahveciler</h1>
          <p>Konumuna göre dükkânları keşfet, isme veya adrese göre ara.</p>
        </div>
      </div>
      <div className="home-search">
          <label className="sr-only" htmlFor="shop-search">
            Dükkân ara
          </label>
          <input
            id="shop-search"
            placeholder="Dükkân veya adres ara"
            value={search}
            onChange={(event) => {
              setLoading(true)
              setError('')
              setSearch(event.target.value)
            }}
          />
      </div>
      {locationNotice && <p className="notice">{locationNotice}</p>}
      {error && <p className="notice notice-error">{error}</p>}
      <div className="discovery-layout">
        <section className="shop-results" aria-label="Dükkân listesi">
          {loading ? (
            <p>Yakındaki dükkânlar yükleniyor…</p>
          ) : shops.length === 0 ? (
            <p className="empty-state">Aramanla eşleşen dükkân bulunamadı.</p>
          ) : (
            shops.map((shop) => (
              <article className="panel shop-card" key={shop.id}>
                <div>
                  <h2>{shop.name}</h2>
                  <p>{shop.address}</p>
                </div>
                <div className="shop-card-meta">
                  <span>★ {shop.rating.toFixed(1)} puan</span>
                  <span>
                    {shop.distance_km === null
                      ? 'Mesafe bilinmiyor'
                      : `${shop.distance_km.toFixed(2)} km`}
                  </span>
                </div>
                <Link
                  className="button button-secondary"
                  to={`/shops/${shop.id}`}
                  state={{ position }}
                >
                  Menüyü Gör
                </Link>
              </article>
            ))
          )}
        </section>
        <section className="map-section" aria-label="Dükkân haritası">
          <ShopMap
            shops={shops}
            center={position}
            userLocation={position}
            userLocationLabel={locationLabel}
          />
        </section>
      </div>
    </section>
  )
}
