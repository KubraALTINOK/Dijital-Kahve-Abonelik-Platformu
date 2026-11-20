import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, api } from '../api/client'
import { useAuth } from '../auth/useAuth'

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { signIn, completeProfile } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [fullName, setFullName] = useState('')
  const [otpRequested, setOtpRequested] = useState(false)
  const [profileRequired, setProfileRequired] = useState(false)
  const [working, setWorking] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  function goToApp() {
    const from = (location.state as { from?: string } | null)?.from ?? '/'
    navigate(from, { replace: true })
  }

  async function handleRequestOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setWorking(true)
    setError('')
    setMessage('')
    try {
      const result = await api.requestOTP(phone)
      setOtpRequested(true)
      setMessage(`${result.message} Geliştirme OTP kodu: ${result.simulated_otp}`)
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : 'Kod istenemedi.')
    } finally {
      setWorking(false)
    }
  }

  async function handleVerifyOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setWorking(true)
    setError('')
    try {
      const user = await signIn(phone, otp)
      if (user.profile_complete) {
        goToApp()
      } else if (mode === 'register' && fullName.trim()) {
        setProfileRequired(true)
        await completeProfile(fullName)
        goToApp()
      } else {
        setProfileRequired(true)
      }
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : 'Giriş yapılamadı.')
    } finally {
      setWorking(false)
    }
  }

  async function handleCompleteProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setWorking(true)
    setError('')
    try {
      await completeProfile(fullName)
      goToApp()
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : 'Profil tamamlanamadı.',
      )
    } finally {
      setWorking(false)
    }
  }

  return (
    <main className="auth-page coffee-auth">
      <section className="panel auth-panel coffee-auth-card">
        <Link className="brand" to="/">
          <span aria-hidden="true">☕</span> KahveCell
        </Link>
        <h1>
          {profileRequired
            ? 'Profilini tamamla'
            : otpRequested
              ? 'Telefonuna gelen 4 haneli kodu gir'
              : mode === 'login'
                ? 'Tekrar hoşgeldin'
                : 'KahveCell’e katıl'}
        </h1>
        {profileRequired ? (
          <form onSubmit={handleCompleteProfile} className="form-stack">
            <label>
              Ad soyad
              <input
                autoComplete="name"
                minLength={2}
                maxLength={100}
                required
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
              />
            </label>
            <button className="button coffee-button" disabled={working}>
              {working ? 'Kaydediliyor…' : 'Profili tamamla'}
            </button>
          </form>
        ) : !otpRequested ? (
          <form onSubmit={handleRequestOtp} className="form-stack">
            <p>
              {mode === 'register'
                ? 'Hesabını oluşturmak için bilgilerini gir.'
                : 'Giriş yapmak için telefon numaranı doğrula.'}
            </p>
            {mode === 'register' && (
              <label>
                Ad soyad
                <input
                  autoComplete="name"
                  minLength={2}
                  maxLength={100}
                  required
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                />
              </label>
            )}
            <label>
              GSM numarası
              <input
                autoComplete="tel"
                inputMode="tel"
                placeholder="+905550000001"
                required
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
              />
            </label>
            <button className="button coffee-button" disabled={working}>
              {working
                ? 'Gönderiliyor…'
                : mode === 'register'
                  ? 'Kayıt için kod gönder'
                  : 'Giriş kodu gönder'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="form-stack">
            <p>{phone} numarasına SMS doğrulaması gönderildi.</p>
            <p className="otp-hint">
              Test notu: Simülasyonda kod her zaman <strong>1234</strong>.
            </p>
            <label>
              OTP kodu
              <input
                autoComplete="one-time-code"
                inputMode="numeric"
                maxLength={4}
                pattern="[0-9]{4}"
                required
                value={otp}
                onChange={(event) => setOtp(event.target.value)}
              />
            </label>
            <button className="button coffee-button" disabled={working}>
              {working ? 'Doğrulanıyor…' : 'Devam et'}
            </button>
            <button
              className="text-button coffee-link"
              type="button"
              onClick={() => {
                setOtpRequested(false)
                setOtp('')
                setMessage('')
              }}
            >
              Telefon numarasını değiştir
            </button>
          </form>
        )}
        {message && <p className="notice">{message}</p>}
        {error && <p className="notice notice-error">{error}</p>}
        {!profileRequired && (
          <p className="auth-switch">
            {mode === 'login' ? 'Hesabın yok mu?' : 'Zaten hesabın var mı?'}{' '}
            <Link to={mode === 'login' ? '/register' : '/login'}>
              {mode === 'login' ? 'Kayıt ol' : 'Giriş yap'}
            </Link>
          </p>
        )}
      </section>
    </main>
  )
}
