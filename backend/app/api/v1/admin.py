from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_roles
from app.models import User
from app.schemas.user import RoleUpdate, UserRead, UserRole

router = APIRouter(
    prefix="/admin",
    tags=["Yönetim"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)


@router.get("/users", response_model=list[UserRead], summary="Kullanıcıları listele")
def list_users(session: Session = Depends(get_db)) -> list[User]:
    return list(session.scalars(select(User).order_by(User.id)))


@router.patch(
    "/users/{user_id}/role",
    response_model=UserRead,
    summary="Kullanıcı rolünü güncelle",
)
def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    session: Session = Depends(get_db),
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    user.role = payload.role.value
    session.commit()
    session.refresh(user)
    return user
