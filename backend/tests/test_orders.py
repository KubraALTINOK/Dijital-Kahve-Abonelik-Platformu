import base64
import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.models import Base, Product, Shop, Subscription, User
from app.schemas.order import OrderCreate
from app.services.orders import create_order, make_qr_payload, order_read_model, verify_order_qr


class OrderServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        event.listen(
            self.engine,
            "connect",
            lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
        )
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.user = User(
            phone_number="+905550000098",
            full_name="Sipariş Test Kullanıcısı",
            role="CUSTOMER",
        )
        self.shop = Shop(
            name="Test Kahve",
            address="Test adres",
            latitude=39.92,
            longitude=32.85,
        )
        self.session.add_all([self.user, self.shop])
        self.session.flush()
        self.product = Product(
            shop_id=self.shop.id,
            name="Latte",
            price=Decimal("100.00"),
        )
        self.subscription = Subscription(
            user_id=self.user.id,
            plan_type="STARTER",
            remaining_credits=2,
            status="ACTIVE",
            started_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        self.session.add_all([self.product, self.subscription])
        self.session.flush()
        self.request = OrderCreate(
            shop_id=self.shop.id,
            product_id=self.product.id,
            size="M",
            sugar=1,
            milk_preference="Yulaf sütü",
            extra_shots=1,
        )

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_creates_signed_qr_and_decrements_one_credit(self) -> None:
        order = create_order(self.session, self.user, self.request)
        self.session.commit()
        self.session.refresh(order)

        payload = make_qr_payload(order)
        self.assertTrue(verify_order_qr(order, payload))
        self.assertEqual(self.subscription.remaining_credits, 1)
        self.assertEqual(payload.shop_id.version, 5)
        self.assertEqual(payload.user_id.version, 5)

        response = order_read_model(order)
        image_bytes = base64.b64decode(response.qr_code_data_url.split(",", 1)[1])
        self.assertTrue(image_bytes.startswith(b"\x89PNG\r\n\x1a\n"))

        forged_payload = payload.model_copy(update={"user_id": uuid4()})
        self.assertFalse(verify_order_qr(order, forged_payload))

    def test_order_is_rejected_when_subscription_is_exhausted(self) -> None:
        self.subscription.remaining_credits = 0
        with self.assertRaises(HTTPException) as raised:
            create_order(self.session, self.user, self.request)
        self.assertEqual(raised.exception.status_code, 409)

    def test_order_is_rejected_without_active_subscription(self) -> None:
        self.subscription.status = "CANCELLED"
        with self.assertRaises(HTTPException) as raised:
            create_order(self.session, self.user, self.request)
        self.assertEqual(raised.exception.status_code, 403)

    def test_unlimited_subscription_does_not_consume_credit(self) -> None:
        self.subscription.plan_type = "UNLIMITED"
        self.subscription.remaining_credits = -1
        create_order(self.session, self.user, self.request)
        self.session.flush()
        self.assertEqual(self.subscription.remaining_credits, -1)


if __name__ == "__main__":
    unittest.main()
