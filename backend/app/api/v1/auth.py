import hmac
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import (
    ACCESS_TOKEN_MINUTES,
    OTP_EXPIRE_MINUTES,
    OTP_MAX_ATTEMPTS,
    REFRESH_TOKEN_DAYS,
    SIMULATED_OTP,
)
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    hash_otp,
    hash_refresh_token,
    is_expired,
    refresh_token_expiry,
)
from app.models import OTPChallenge, RefreshToken, User
from app.schemas.auth import OTPRequested, OTPVerifyRequest, PhoneRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama"])


def issue_tokens(session: Session, user: User) -> TokenResponse:
    refresh_value = create_refresh_token_value()
    now = datetime.now(UTC)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_value),
            created_at=now,
            expires_at=refresh_token_expiry(),
        )
    )
    return TokenResponse(
        access_token=create_access_token(user.id),
        access_token_expires_in=ACCESS_TOKEN_MINUTES * 60,
        refresh_token=refresh_value,
        refresh_token_expires_in=REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        user=user,
    )


@router.post(
    "/register",
    response_model=OTPRequested,
    summary="Kayıt veya giriş için OTP iste",
    description=(
        "SMS gönderimi simüle edilir. Case gereği sabit OTP 1234 kullanılır; "
        "mevcut ve yeni numaralar aynı akışı izler."
    ),
)
def request_otp(payload: PhoneRequest, session: Session = Depends(get_db)) -> OTPRequested:
    now = datetime.now(UTC)
    session.add(
        OTPChallenge(
            phone_number=payload.phone_number,
            code_hash=hash_otp(payload.phone_number),
            created_at=now,
            expires_at=now + timedelta(minutes=OTP_EXPIRE_MINUTES),
        )
    )
    session.commit()
    return OTPRequested(
        message="Doğrulama kodu gönderimi simüle edildi.",
        expires_in_seconds=OTP_EXPIRE_MINUTES * 60,
        simulated_otp=SIMULATED_OTP,
    )


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    summary="OTP doğrula ve oturum aç",
)
def verify_otp(
    payload: OTPVerifyRequest, session: Session = Depends(get_db)
) -> TokenResponse:
    challenge = session.scalar(
        select(OTPChallenge)
        .where(OTPChallenge.phone_number == payload.phone_number)
        .order_by(OTPChallenge.id.desc())
    )
    if (
        challenge is None
        or challenge.consumed_at is not None
        or is_expired(challenge.expires_at)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doğrulama kodu bulunamadı, süresi doldu veya daha önce kullanıldı.",
        )
    if challenge.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Doğrulama denemesi sınırına ulaşıldı; yeni kod isteyin.",
        )
    if not hmac.compare_digest(
        challenge.code_hash, hash_otp(payload.phone_number, payload.otp_code)
    ):
        challenge.attempts += 1
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doğrulama kodu hatalı.",
        )

    user = session.scalar(
        select(User).where(User.phone_number == payload.phone_number)
    )
    if user is None:
        user = User(
            phone_number=payload.phone_number,
            full_name="",
            role="CUSTOMER",
            profile_complete=False,
        )
        session.add(user)
        session.flush()

    challenge.consumed_at = datetime.now(UTC)
    token_response = issue_tokens(session, user)
    session.commit()
    session.refresh(user)
    return token_response


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Erişim token'ını yenile",
)
def refresh_access_token(
    payload: RefreshRequest, session: Session = Depends(get_db)
) -> TokenResponse:
    token_record = session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)
        )
    )
    if (
        token_record is None
        or token_record.revoked_at is not None
        or is_expired(token_record.expires_at)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token geçersiz veya süresi dolmuş.",
        )

    user = session.get(User, token_record.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bu token'a bağlı kullanıcı bulunamadı.",
        )

    token_record.revoked_at = datetime.now(UTC)
    token_response = issue_tokens(session, user)
    session.commit()
    return token_response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Oturumu kapat",
)
def logout(
    payload: RefreshRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    token_record = session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(payload.refresh_token),
            RefreshToken.user_id == current_user.id,
        )
    )
    if token_record is not None and token_record.revoked_at is None:
        token_record.revoked_at = datetime.now(UTC)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
