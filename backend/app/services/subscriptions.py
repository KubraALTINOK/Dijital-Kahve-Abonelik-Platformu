from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment, Subscription, User
from app.schemas.subscription import (
    PaymentResult,
    SubscriptionPlan,
    SubscriptionRead,
)

PLAN_DETAILS = {
    SubscriptionPlan.STARTER: {
        "name": "Starter",
        "price": Decimal("89.99"),
        "credits": 10,
        "guest_passes": 0,
        "priority_service": False,
    },
    SubscriptionPlan.PREMIUM: {
        "name": "Premium",
        "price": Decimal("149.99"),
        "credits": 20,
        "guest_passes": 2,
        "priority_service": False,
    },
    SubscriptionPlan.UNLIMITED: {
        "name": "Unlimited",
        "price": Decimal("249.99"),
        "credits": None,
        "guest_passes": 5,
        "priority_service": True,
    },
}

SUCCESS_TEST_CARD = "4242424242424242"
FAILURE_TEST_CARD = "4000000000000002"


def build_payment_result(
    payment: Payment, subscription: Subscription | None
) -> PaymentResult:
    return PaymentResult(
        success=payment.status == "SUCCESS",
        transaction_id=payment.transaction_id,
        amount=payment.amount,
        timestamp=payment.created_at,
        message=(
            "Ödeme başarılı; abonelik etkinleştirildi."
            if payment.status == "SUCCESS"
            else "Ödeme başarısız; aktif abonelik değişmedi."
        ),
        subscription=SubscriptionRead.model_validate(subscription)
        if subscription is not None
        else None,
    )


def current_active_subscription(session: Session, user_id: int) -> Subscription | None:
    return session.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "ACTIVE",
        )
        .order_by(Subscription.id.desc())
    )


def process_subscription_payment(
    session: Session,
    user: User,
    plan: SubscriptionPlan,
    card_number: str,
) -> tuple[Payment, Subscription | None]:
    plan_details = PLAN_DETAILS[plan]
    now = datetime.now(UTC)
    subscription = current_active_subscription(session, user.id)
    payment_succeeded = card_number == SUCCESS_TEST_CARD
    payment = Payment(
        transaction_id=str(uuid4()),
        user_id=user.id,
        subscription_id=subscription.id if subscription else None,
        subscription_plan=plan.value,
        amount=plan_details["price"],
        status="SUCCESS" if payment_succeeded else "FAILED",
        card_last_four=card_number[-4:],
        created_at=now,
    )
    session.add(payment)

    if not payment_succeeded:
        return payment, subscription

    if subscription is None:
        subscription = Subscription(
            user_id=user.id,
            plan_type=plan.value,
            remaining_credits=0,
            status="ACTIVE",
            started_at=now,
            expires_at=now + timedelta(days=30),
        )
        session.add(subscription)
        session.flush()
    else:
        subscription.plan_type = plan.value
        subscription.started_at = now
        subscription.expires_at = now + timedelta(days=30)

    subscription.remaining_credits = (
        -1 if plan_details["credits"] is None else plan_details["credits"]
    )
    payment.subscription_id = subscription.id
    return payment, subscription
