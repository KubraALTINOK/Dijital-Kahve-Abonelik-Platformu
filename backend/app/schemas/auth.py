from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead

PHONE_PATTERN = r"^\+[1-9]\d{7,14}$"


class PhoneRequest(BaseModel):
    phone_number: str = Field(pattern=PHONE_PATTERN)


class OTPVerifyRequest(PhoneRequest):
    otp_code: str = Field(pattern=r"^\d{4}$")


class OTPRequested(BaseModel):
    message: str
    expires_in_seconds: int
    simulated_otp: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
    access_token_expires_in: int
    refresh_token: str
    refresh_token_expires_in: int
    user: UserRead
