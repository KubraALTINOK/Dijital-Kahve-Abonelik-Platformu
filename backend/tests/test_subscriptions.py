import unittest
from decimal import Decimal

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.models import Base, Payment, Subscription, User
from app.schemas.subscription import SubscriptionPlan
from app.services.subscriptions import (
    FAILURE_TEST_CARD,
    PLAN_DETAILS,
    SUCCESS_TEST_CARD,
    process_subscription_payment,
)


class SubscriptionPaymentTests(unittest.TestCase):
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
            phone_number="+905550000099",
            full_name="Test Kullanıcısı",
        )
        self.session.add(self.user)
        self.session.flush()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_failed_payment_keeps_existing_plan_and_credits(self) -> None:
        _, subscription = process_subscription_payment(
            self.session, self.user, SubscriptionPlan.STARTER, SUCCESS_TEST_CARD
        )
        self.session.commit()
        self.assertIsNotNone(subscription)
        assert subscription is not None
        original_start = subscription.started_at

        payment, unchanged_subscription = process_subscription_payment(
            self.session, self.user, SubscriptionPlan.PREMIUM, FAILURE_TEST_CARD
        )
        self.session.commit()

        self.assertEqual(payment.status, "FAILED")
        self.assertEqual(payment.amount, Decimal("149.99"))
        self.assertIs(unchanged_subscription, subscription)
        self.assertEqual(subscription.plan_type, "STARTER")
        self.assertEqual(subscription.remaining_credits, 10)
        self.assertEqual(subscription.started_at, original_start)

    def test_successful_upgrade_and_unlimited_credit_representation(self) -> None:
        _, subscription = process_subscription_payment(
            self.session, self.user, SubscriptionPlan.STARTER, SUCCESS_TEST_CARD
        )
        self.session.commit()
        assert subscription is not None

        payment, upgraded = process_subscription_payment(
            self.session, self.user, SubscriptionPlan.PREMIUM, SUCCESS_TEST_CARD
        )
        self.session.commit()
        self.assertEqual(payment.status, "SUCCESS")
        self.assertEqual(upgraded.plan_type, "PREMIUM")
        self.assertEqual(upgraded.remaining_credits, 20)

        _, unlimited = process_subscription_payment(
            self.session, self.user, SubscriptionPlan.UNLIMITED, SUCCESS_TEST_CARD
        )
        self.session.commit()
        self.assertEqual(unlimited.remaining_credits, -1)
        self.assertIsNone(PLAN_DETAILS[SubscriptionPlan.UNLIMITED]["credits"])
        self.assertEqual(
            self.session.scalar(select(Subscription).where(Subscription.user_id == self.user.id)),
            subscription,
        )

    def test_plan_prices_and_monthly_entitlements(self) -> None:
        self.assertEqual(PLAN_DETAILS[SubscriptionPlan.STARTER]["price"], Decimal("89.99"))
        self.assertEqual(PLAN_DETAILS[SubscriptionPlan.STARTER]["credits"], 10)
        self.assertEqual(PLAN_DETAILS[SubscriptionPlan.PREMIUM]["price"], Decimal("149.99"))
        self.assertEqual(PLAN_DETAILS[SubscriptionPlan.PREMIUM]["credits"], 20)
        self.assertEqual(PLAN_DETAILS[SubscriptionPlan.PREMIUM]["guest_passes"], 2)
        self.assertEqual(PLAN_DETAILS[SubscriptionPlan.UNLIMITED]["price"], Decimal("249.99"))
        self.assertEqual(PLAN_DETAILS[SubscriptionPlan.UNLIMITED]["guest_passes"], 5)
        self.assertTrue(PLAN_DETAILS[SubscriptionPlan.UNLIMITED]["priority_service"])

        _, subscription = process_subscription_payment(
            self.session, self.user, SubscriptionPlan.STARTER, SUCCESS_TEST_CARD
        )
        self.assertIsNotNone(subscription.expires_at)
        self.assertGreater(subscription.expires_at, subscription.started_at)


if __name__ == "__main__":
    unittest.main()
