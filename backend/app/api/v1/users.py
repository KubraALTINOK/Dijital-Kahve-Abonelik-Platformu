from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.user import ProfileUpdate, UserRead

router = APIRouter(prefix="/users", tags=["Kullanıcılar"])


@router.get("/me", response_model=UserRead, summary="Giriş yapan kullanıcı")
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="İlk profili tamamla veya güncelle",
)
def update_current_user(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> User:
    current_user.full_name = payload.full_name.strip()
    current_user.profile_complete = True
    fields = payload.model_fields_set
    if "email" in fields:
        current_user.email = payload.email
    if payload.coffee_preferences is not None:
        current_user.coffee_preferences = payload.coffee_preferences
    if payload.allergens is not None:
        current_user.allergens = payload.allergens
    session.commit()
    session.refresh(current_user)
    return current_user
