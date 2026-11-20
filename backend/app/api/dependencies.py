from collections.abc import Callable, Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import JWT_SECRET_KEY
from app.db.database import SessionLocal
from app.models import User
from app.schemas.user import UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçerli bir erişim token'ı gerekli.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.InvalidTokenError as exc:
        raise unauthorized from exc

    if payload.get("type") != "access":
        raise unauthorized

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.isdecimal():
        raise unauthorized

    user = session.get(User, int(user_id))
    if user is None:
        raise unauthorized
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in {role.value for role in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için rol yetkiniz yok.",
            )
        return current_user

    return role_checker
