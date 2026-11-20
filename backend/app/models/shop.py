from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product
    from app.models.user import User


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    working_hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    owner: Mapped["User | None"] = relationship()
    products: Mapped[list["Product"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="shop")
