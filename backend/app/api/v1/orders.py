from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_roles
from app.models import Order, Shop, User
from app.schemas.order import (
    OrderCreate,
    OrderRead,
    OrderStatus,
    OrderStatusUpdate,
    QRPayload,
    QRVerificationResult,
)
from app.schemas.user import UserRole
from app.services.orders import create_order, order_read_model, verify_order_qr

router = APIRouter(prefix="/orders", tags=["Siparişler"])


def _shop_owner_order(
    session: Session,
    order_id: int,
    current_user: User,
) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    if order.shop.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu sipariş, size atanmış dükkâna ait değil.",
        )
    return order


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Abonelik hakkıyla kahve siparişi oluştur",
)
def create_customer_order(
    payload: OrderCreate,
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
    session: Session = Depends(get_db),
) -> OrderRead:
    order = create_order(session, current_user, payload)
    session.commit()
    session.refresh(order)
    return order_read_model(order)


@router.get(
    "/history",
    response_model=list[OrderRead],
    summary="Müşterinin sipariş geçmişi",
)
def read_order_history(
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
    session: Session = Depends(get_db),
) -> list[OrderRead]:
    orders = session.scalars(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return [order_read_model(order) for order in orders]


@router.get(
    "/shop",
    response_model=list[OrderRead],
    summary="Dükkân sahibinin siparişlerini listele",
)
def read_shop_orders(
    current_user: User = Depends(require_roles(UserRole.SHOP_OWNER)),
    session: Session = Depends(get_db),
) -> list[OrderRead]:
    orders = session.scalars(
        select(Order)
        .join(Shop, Order.shop_id == Shop.id)
        .where(Shop.owner_user_id == current_user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return [order_read_model(order) for order in orders]


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Sipariş detayını ve QR kodunu gör",
)
def read_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> OrderRead:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    is_customer = order.user_id == current_user.id
    is_assigned_shop_owner = order.shop.owner_user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN.value
    if not (is_customer or is_assigned_shop_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu siparişe erişim yetkiniz yok.",
        )
    return order_read_model(order)


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Sipariş durumunu bir sonraki aşamaya geçir",
)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: User = Depends(require_roles(UserRole.SHOP_OWNER)),
    session: Session = Depends(get_db),
) -> OrderRead:
    order = _shop_owner_order(session, order_id, current_user)
    next_status = {
        OrderStatus.PENDING: OrderStatus.ACCEPTED,
        OrderStatus.ACCEPTED: OrderStatus.PREPARING,
        OrderStatus.PREPARING: OrderStatus.READY,
    }
    expected_status = next_status.get(OrderStatus(order.status))
    if payload.status == OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teslim edildi durumuna geçmek için QR kodunu doğrulayın.",
        )
    if payload.status != expected_status:
        expected_value = expected_status.value if expected_status is not None else "yok"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bu sipariş için izin verilen sonraki durum: {expected_value}.",
        )

    order.status = payload.status.value
    session.commit()
    session.refresh(order)
    return order_read_model(order)


@router.post(
    "/verify-qr",
    response_model=QRVerificationResult,
    summary="QR imzasını doğrula ve siparişi teslim et",
)
def verify_qr_and_deliver(
    payload: QRPayload,
    current_user: User = Depends(require_roles(UserRole.SHOP_OWNER)),
    session: Session = Depends(get_db),
) -> QRVerificationResult:
    order = session.scalar(
        select(Order).where(Order.qr_order_id == str(payload.order_id))
    )
    if order is None:
        raise HTTPException(status_code=400, detail="QR kodu doğrulanamadı.")
    order = _shop_owner_order(session, order.id, current_user)
    if not verify_order_qr(order, payload):
        raise HTTPException(status_code=400, detail="QR imzası geçersiz.")
    if order.status != OrderStatus.READY.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sipariş hazır olmadan QR ile teslim edilemez.",
        )

    order.status = OrderStatus.DELIVERED.value
    order.delivered_at = datetime.now(UTC)
    session.commit()
    session.refresh(order)
    return QRVerificationResult(
        valid=True,
        message="QR imzası doğrulandı; sipariş teslim edildi.",
        order=order_read_model(order),
    )
