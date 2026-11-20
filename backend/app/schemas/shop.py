from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    category: str


class ShopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    working_hours: str | None
    rating: float
    distance_km: float | None = None


class ShopDetail(ShopRead):
    menu: list[ProductRead]
