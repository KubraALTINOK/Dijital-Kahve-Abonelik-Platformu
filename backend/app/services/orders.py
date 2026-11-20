import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from io import BytesIO
from uuid import NAMESPACE_URL, uuid4, uuid5

import qrcode
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import QR_SIGNING_SECRET
from app.models import Order, Product, Shop, Subscription, User
from app.schemas.order import OrderCreate, OrderRead, QRPayload
from app.schemas.shop import ProductRead, ShopRead


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _public_entity_id(entity: str, internal_id: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"kahvecell:{entity}:{internal_id}"))


def _unsigned_qr_payload(order: Order) -> dict[str, str]:
    if order.qr_order_id is None:
        raise RuntimeError(f"Sipariş {order.id} için QR kimliği oluşturulmamış.")
    if order.created_at is None:
        raise RuntimeError(f"Sipariş {order.id} için oluşturulma tarihi bulunamadı.")
    return {
        "order_id": order.qr_order_id,
        "user_id": _public_entity_id("user", order.user_id),
        "shop_id": _public_entity_id("shop", order.shop_id),
        "created_at": _as_utc(order.created_at).isoformat(),
    }


def _sign_payload(payload: dict[str, str]) -> str:
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        QR_SIGNING_SECRET.encode(),
        canonical_json.encode(),
        hashlib.sha256,
    ).hexdigest()


def make_qr_payload(order: Order) -> QRPayload:
    unsigned_payload = _unsigned_qr_payload(order)
    signature = order.qr_signature or _sign_payload(unsigned_payload)
    return QRPayload(**unsigned_payload, signature=signature)


def _qr_code_data_url(payload: QRPayload) -> str:
    qr_content = json.dumps(
        payload.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    image = qrcode.make(qr_content)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def order_read_model(order: Order) -> OrderRead:
    if order.qr_signature is None:
        raise RuntimeError(f"Sipariş {order.id} için QR imzası bulunamadı.")
    qr_payload = make_qr_payload(order)
    return OrderRead(
        id=order.id,
        user_id=order.user_id,
        shop_id=order.shop_id,
        product_id=order.product_id,
        status=order.status,
        size=order.size,
        sugar=order.sugar,
        milk_preference=order.milk_preference,
        extra_shots=order.extra_shots,
        created_at=_as_utc(order.created_at),
        shop=ShopRead.model_validate(order.shop),
        product=ProductRead.model_validate(order.product),
        qr_payload=qr_payload,
        qr_code_data_url=_qr_code_data_url(qr_payload),
    )


def create_order(
    session: Session,
    current_user: User,
    payload: OrderCreate,
) -> Order:
    now = datetime.now(UTC)
    subscription = session.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.status == "ACTIVE",
        )
        .order_by(Subscription.id.desc())
        .with_for_update()
    )
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sipariş vermek için aktif bir aboneliğiniz olmalıdır.",
        )
    if subscription.expires_at is not None and _as_utc(subscription.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aboneliğinizin süresi dolmuş. Sipariş vermeden önce yenileyin.",
        )
    if subscription.remaining_credits == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aylık kahve hakkınız bitmiş. Sipariş vermek için paketinizi yenileyin.",
        )
    if subscription.remaining_credits < 0 and subscription.plan_type != "UNLIMITED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Abonelik kahve hakkı geçersiz durumda.",
        )

    shop = session.get(Shop, payload.shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı.")
    product = session.get(Product, payload.product_id)
    if product is None or product.shop_id != shop.id:
        raise HTTPException(
            status_code=404,
            detail="Seçilen ürün bu dükkânın menüsünde bulunamadı.",
        )

    order = Order(
        user_id=current_user.id,
        shop_id=shop.id,
        product_id=product.id,
        status="PENDING",
        size=payload.size.value,
        sugar=payload.sugar,
        milk_preference=payload.milk_preference,
        extra_shots=payload.extra_shots,
        qr_order_id=str(uuid4()),
        created_at=now,
    )
    session.add(order)
    session.flush()

    order.qr_signature = _sign_payload(_unsigned_qr_payload(order))
    if subscription.remaining_credits != -1:
        subscription.remaining_credits -= 1
    session.flush()
    return order


def verify_order_qr(order: Order, supplied_payload: QRPayload) -> bool:
    expected_unsigned_payload = _unsigned_qr_payload(order)
    expected_signature = _sign_payload(expected_unsigned_payload)
    expected_payload = QRPayload(
        **expected_unsigned_payload,
        signature=expected_signature,
    )
    return (
        order.qr_signature is not None
        and hmac.compare_digest(order.qr_signature, expected_signature)
        and hmac.compare_digest(supplied_payload.signature, expected_signature)
        and supplied_payload.model_dump() == expected_payload.model_dump()
    )
