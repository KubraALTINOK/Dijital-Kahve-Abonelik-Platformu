from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionPlan(str, Enum):
    STARTER = "STARTER"
    PREMIUM = "PREMIUM"
    UNLIMITED = "UNLIMITED"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class PlanRead(BaseModel):
    plan_type: SubscriptionPlan
    name: str
    monthly_price: Decimal
    coffee_credits: int | None
    guest_passes: int
    priority_service: bool


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_type: SubscriptionPlan
    remaining_credits: int = Field(
        description="-1 means unlimited; 0 means no coffee credits remain."
    )
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime | None


class SubscriptionPurchase(BaseModel):
    subscription_plan: SubscriptionPlan
    card_number: str = Field(
        pattern=r"^(4242424242424242|4000000000000002)$",
        description=(
            "Test kartı: 4242424242424242 başarılı; "
            "4000000000000002 başarısız."
        ),
    )


class PaymentRead(BaseModel):
    id: int
    transaction_id: str
    subscription_plan: SubscriptionPlan
    amount: Decimal
    status: str
    card_last_four: str
    created_at: datetime


class PaymentResult(BaseModel):
    success: bool
    transaction_id: str
    amount: Decimal
    timestamp: datetime
    message: str
    subscription: SubscriptionRead | None = None
