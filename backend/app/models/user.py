from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, JSON, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.subscription import Subscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="CUSTOMER")
    profile_complete: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("0"), nullable=False
    )
    coffee_preferences: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default=text("'[]'"), nullable=False
    )
    allergens: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default=text("'[]'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
