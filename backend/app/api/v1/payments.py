from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import Payment, User
from app.schemas.subscription import (
    PaymentRead,
    PaymentResult,
    SubscriptionPurchase,
)
from app.services.subscriptions import (
    build_payment_result,
    process_subscription_payment,
)

router = APIRouter(prefix="/payments", tags=["Paycell Ödeme Simülasyonu"])


@router.post(
    "/process",
    response_model=PaymentResult,
    summary="Paycell ödeme simülasyonu",
)
def process_payment(
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
    "/history",
    response_model=list[PaymentRead],
    summary="Ödeme geçmişimi gör",
)
def read_payment_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[Payment]:
    return list(
        session.scalars(
            select(Payment)
            .where(Payment.user_id == current_user.id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
        )
    )
