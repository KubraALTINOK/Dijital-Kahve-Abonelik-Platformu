from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.shop import Shop
    from app.models.user import User


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    size: Mapped[str] = mapped_column(String(1), default="M")
    sugar: Mapped[int] = mapped_column(Integer, default=0)
    milk_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extra_shots: Mapped[int] = mapped_column(Integer, default=0)
    qr_order_id: Mapped[str | None] = mapped_column(
        String(36), unique=True, index=True, nullable=True
    )
    qr_signature: Mapped[str | None] = mapped_column(String(64), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    shop: Mapped["Shop"] = relationship(back_populates="orders")
    product: Mapped["Product"] = relationship(back_populates="orders")
