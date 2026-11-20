import { useEffect } from 'react'
import { divIcon } from 'leaflet'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'
import type { Shop } from '../api/types'

const ANKARA_CENTER: [number, number] = [39.9206, 32.8541]

const shopIcon = divIcon({
  className: 'shop-map-marker',
  html: '<span aria-hidden="true"></span>',
  iconSize: [28, 36],
  iconAnchor: [14, 36],
  popupAnchor: [0, -34],
})

const userIcon = divIcon({
  className: 'user-map-marker',
  html: '<span aria-hidden="true"></span>',
  iconSize: [28, 36],
  iconAnchor: [14, 36],
  popupAnchor: [0, -34],
})

function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap()

  useEffect(() => {
    map.setView(center)
  }, [center, map])

  return null
}

export function ShopMap({
  shops,
  center,
  userLocation,
  userLocationLabel = 'Konumunuz',
}: {
  shops: Shop[]
  center?: [number, number]
  userLocation?: [number, number]
  userLocationLabel?: string
}) {
  return (
    <MapContainer
      className="shop-map"
      center={center ?? ANKARA_CENTER}
      zoom={12}
      scrollWheelZoom={false}
    >
      <MapRecenter center={center ?? ANKARA_CENTER} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {userLocation && (
        <Marker position={userLocation} icon={userIcon}>
          <Popup>{userLocationLabel}</Popup>
        </Marker>
      )}
      {shops.map((shop) => (
        <Marker
          key={shop.id}
          position={[shop.latitude, shop.longitude]}
          icon={shopIcon}
          zIndexOffset={1000}
        >
          <Popup>
            <strong>{shop.name}</strong>
            <br />
            {shop.address}
            <br />
            <Link to={`/shops/${shop.id}`} state={{ position: userLocation }}>
              Dükkânı gör
            </Link>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
