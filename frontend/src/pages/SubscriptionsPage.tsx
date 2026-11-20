import { useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import type { Plan, Subscription } from '../api/types'

export function SubscriptionsPage() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [cardNumber, setCardNumber] = useState('4242424242424242')
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function load() {
    try {
      const availablePlans = await api.plans()
      setPlans(availablePlans)
      try {
        setSubscription(await api.mySubscription())
      } catch (reason) {
        if (reason instanceof ApiError && reason.status === 404) {
          setSubscription(null)
        } else {
          throw reason
        }
      }
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : 'Paketler yüklenemedi.',
      )
    }
  }

  useEffect(() => {
    let active = true
    api
      .plans()
      .then((availablePlans) => {
        if (active) setPlans(availablePlans)
        return api
          .mySubscription()
          .then((currentSubscription) => {
            if (active) setSubscription(currentSubscription)
          })
          .catch((reason: unknown) => {
            if (active && reason instanceof ApiError && reason.status === 404) {
              setSubscription(null)
              return
            }
            if (active) {
              setError(
                reason instanceof ApiError
                  ? reason.message
                  : 'Abonelik yüklenemedi.',
              )
            }
          })
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(
            reason instanceof ApiError ? reason.message : 'Paketler yüklenemedi.',
          )
        }
      })
    return () => {
      active = false
    }
  }, [])

  async function buyPlan(event: FormEvent<HTMLFormElement>, plan: Plan) {
    event.preventDefault()
    setWorking(true)
    setError('')
    setMessage('')
    try {
      const result = subscription
        ? await api.changePlan(plan.plan_type, cardNumber)
        : await api.purchasePlan(plan.plan_type, cardNumber)
      if (!result.success) {
        setError(result.message)
      } else {
        setMessage(`${plan.name} aboneliğin etkinleştirildi.`)
        await load()
      }
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : 'Ödeme tamamlanamadı.',
      )
    } finally {
      setWorking(false)
    }
  }

  async function cancelSubscription() {
    setWorking(true)
    setError('')
    setMessage('')
    try {
      await api.cancelSubscription()
      setSubscription(null)
      setMessage('Aboneliğin iptal edildi.')
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : 'Abonelik iptal edilemedi.',
      )
    } finally {
      setWorking(false)
    }
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Kahve planları</p>
          <h1>Aboneliğin</h1>
          <p>Ödeme simülasyonudur; gerçek kart bilgisi girme.</p>
        </div>
      </div>
      {subscription && (
        <div className="panel current-plan">
          <div>
            <strong>Aktif paket: {subscription.plan_type}</strong>
            <p>
              {subscription.remaining_credits === -1
                ? 'Sınırsız kahve'
                : `${subscription.remaining_credits} kahve hakkı`}
            </p>
          </div>
          <button
            className="button button-secondary"
            disabled={working}
            onClick={cancelSubscription}
          >
            Aboneliği iptal et
          </button>
        </div>
      )}
      <label className="card-input">
        Test kart numarası
        <input
          inputMode="numeric"
          pattern="[0-9]{16}"
          value={cardNumber}
          onChange={(event) => setCardNumber(event.target.value)}
        />
        <small>Başarılı: 4242424242424242 · Başarısız: 4000000000000002</small>
      </label>
      {message && <p className="notice">{message}</p>}
      {error && <p className="notice notice-error">{error}</p>}
      <div className="plan-grid">
        {plans.map((plan) => (
          <article className="panel plan-card" key={plan.plan_type}>
            <div>
              <h2>{plan.name}</h2>
              <p className="plan-price">{Number(plan.monthly_price).toFixed(2)} TL / ay</p>
              <ul>
                <li>
                  {plan.coffee_credits === null
                    ? 'Sınırsız kahve'
                    : `${plan.coffee_credits} kahve / ay`}
                </li>
                <li>{plan.guest_passes} misafir hakkı</li>
                {plan.priority_service && <li>Öncelikli hizmet</li>}
                <li>Tüm dükkânlarda geçerli</li>
              </ul>
            </div>
            <form onSubmit={(event) => void buyPlan(event, plan)}>
              <button className="button" disabled={working}>
                {subscription ? 'Paketi seç' : 'Satın al'}
              </button>
            </form>
          </article>
        ))}
      </div>
    </section>
  )
}
