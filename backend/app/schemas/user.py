from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    SHOP_OWNER = "SHOP_OWNER"
    ADMIN = "ADMIN"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone_number: str
    full_name: str
    email: str | None
    role: UserRole
    profile_complete: bool
    coffee_preferences: list[str]
    allergens: list[str]


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    coffee_preferences: list[str] | None = None
    allergens: list[str] | None = None


class RoleUpdate(BaseModel):
    role: UserRole
