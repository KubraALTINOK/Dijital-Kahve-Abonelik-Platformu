import { Link, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { AppLayout } from './components/AppLayout'
import { RequireAuth } from './components/RequireAuth'
import { AuthPage } from './pages/AuthPage'
import { HomePage } from './pages/HomePage'
import { NewOrderPage } from './pages/NewOrderPage'
import { OrderHistoryPage } from './pages/OrderHistoryPage'
import { QRCodePage } from './pages/QRCodePage'
import { ShopDetailPage } from './pages/ShopDetailPage'
import { SubscriptionsPage } from './pages/SubscriptionsPage'

function NotFoundPage() {
  return (
    <section className="panel not-found">
      <h1>Sayfa bulunamadı</h1>
      <Link to="/">Ana sayfaya dön</Link>
    </section>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="shops" element={<Navigate to="/" replace />} />
          <Route path="shops/:shopId" element={<ShopDetailPage />} />
          <Route path="orders/new" element={<NewOrderPage />} />
          <Route path="orders/:orderId/qr" element={<QRCodePage />} />
          <Route path="orders/history" element={<OrderHistoryPage />} />
          <Route path="subscriptions" element={<SubscriptionsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
