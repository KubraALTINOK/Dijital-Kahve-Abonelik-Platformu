from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import Subscription, User
from app.schemas.subscription import (
    PaymentResult,
    PlanRead,
    SubscriptionPlan,
    SubscriptionPurchase,
    SubscriptionRead,
)
from app.services.subscriptions import (
    PLAN_DETAILS,
    build_payment_result,
    current_active_subscription,
    process_subscription_payment,
)

router = APIRouter(prefix="/subscriptions", tags=["Abonelikler"])


@router.get(
    "/plans",
    response_model=list[PlanRead],
    summary="Abonelik paketlerini listele",
)
def list_plans() -> list[PlanRead]:
    return [
        PlanRead(
            plan_type=plan,
            name=details["name"],
            monthly_price=details["price"],
            coffee_credits=details["credits"],
            guest_passes=details["guest_passes"],
            priority_service=details["priority_service"],
        )
        for plan, details in PLAN_DETAILS.items()
    ]


@router.post(
    "",
    response_model=PaymentResult,
    summary="Ödeme simülasyonuyla abonelik başlat",
)
def create_subscription(
    payload: SubscriptionPurchase,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> PaymentResult:
    payment, subscription = process_subscription_payment(
        session, current_user, payload.subscription_plan, payload.card_number
    )
    session.commit()
    if subscription is not None:
        session.refresh(subscription)
    session.refresh(payment)
    return build_payment_result(payment, subscription)


@router.get(
    "/me",
    response_model=SubscriptionRead,
    summary="Aktif aboneliğimi gör",
)
def read_my_subscription(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Subscription:
    subscription = current_active_subscription(session, current_user.id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı.")
    return subscription


@router.patch(
    "/me",
    response_model=PaymentResult,
    summary="Aboneliği yükselt veya düşür",
)
def change_my_subscription(
    payload: SubscriptionPurchase,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> PaymentResult:
    if current_active_subscription(session, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Değiştirilecek aktif abonelik yok.")
    payment, subscription = process_subscription_payment(
        session, current_user, payload.subscription_plan, payload.card_number
    )
    session.commit()
    if subscription is not None:
        session.refresh(subscription)
    session.refresh(payment)
    return build_payment_result(payment, subscription)


@router.delete(
    "/me",
    response_model=SubscriptionRead,
    summary="Aboneliği hemen iptal et",
)
def cancel_my_subscription(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Subscription:
    subscription = current_active_subscription(session, current_user.id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="İptal edilecek aktif abonelik yok.")
    now = datetime.now(UTC)
    subscription.status = "CANCELLED"
    subscription.remaining_credits = 0
    subscription.expires_at = now
    session.commit()
    session.refresh(subscription)
    return subscription
