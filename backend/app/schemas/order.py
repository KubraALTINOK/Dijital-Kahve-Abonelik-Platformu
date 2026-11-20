from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.shop import ProductRead, ShopRead


class CoffeeSize(str, Enum):
    S = "S"
    M = "M"
    L = "L"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERED = "DELIVERED"


class OrderCreate(BaseModel):
    shop_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    size: CoffeeSize = CoffeeSize.M
    sugar: int = Field(default=0, ge=0, le=5)
    milk_preference: str | None = Field(default=None, max_length=50)
    extra_shots: int = Field(default=0, ge=0, le=3)


class QRPayload(BaseModel):
    order_id: UUID
    user_id: UUID
    shop_id: UUID
    created_at: datetime
    signature: str = Field(pattern=r"^[0-9a-f]{64}$")


class OrderRead(BaseModel):
    id: int
    user_id: int
    shop_id: int
    product_id: int
    status: OrderStatus
    size: CoffeeSize
    sugar: int
    milk_preference: str | None
    extra_shots: int
    created_at: datetime
    shop: ShopRead
    product: ProductRead
    qr_payload: QRPayload
    qr_code_data_url: str


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class QRVerificationResult(BaseModel):
    valid: bool
    message: str
    order: OrderRead


