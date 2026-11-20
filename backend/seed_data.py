"""Seed Ankara demo shops, menus, and a case-compatible OTP test account.

Shop names and coordinates are based on OpenStreetMap data
(© OpenStreetMap contributors, ODbL 1.0).
Menu prices are illustrative demo values, not verified live prices.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.models import Base, Product, Shop, Subscription, User

TEST_PHONE_NUMBER = "+905550000001"
TEST_USER_NAME = "KahveCell Test Kullanıcısı"
TEST_PLAN = "STARTER"
TEST_CREDITS = 10


class ShopSeedData(TypedDict):
    name: str
    address: str
    latitude: float
    longitude: float
    prices: tuple[Decimal, ...]


SHOPS: list[ShopSeedData] = [
    {
        "name": "CoffeeLab",
        "address": "5A, Tuna Caddesi, Cumhuriyet Mahallesi, Kızılay, Çankaya, Ankara",
        "latitude": 39.9232981,
        "longitude": 32.8554392,
        "prices": (Decimal("120"), Decimal("145"), Decimal("165"), Decimal("135"), Decimal("175")),
    },
    {
        "name": "Caffe'de Neo",
        "address": "Sakarya Caddesi, Cumhuriyet Mahallesi, Kızılay, Çankaya, Ankara",
        "latitude": 39.9218674,
        "longitude": 32.8548316,
        "prices": (Decimal("115"), Decimal("140"), Decimal("160"), Decimal("130"), Decimal("170")),
    },
    {
        "name": "Coffee LAB Bahçeli 71",
        "address": "71. Sokak, Yukarı Bahçelievler Mahallesi, Çankaya, Ankara",
        "latitude": 39.9212036,
        "longitude": 32.8273697,
        "prices": (Decimal("110"), Decimal("135"), Decimal("155"), Decimal("125"), Decimal("165")),
    },
    {
        "name": "Cafe des Cafes",
        "address": "83, Tunalı Hilmi Caddesi, Barbaros Mahallesi, Çankaya, Ankara",
        "latitude": 39.9066216,
        "longitude": 32.8612044,
        "prices": (Decimal("125"), Decimal("150"), Decimal("170"), Decimal("140"), Decimal("180")),
    },
    {
        "name": "Arabica Coffee House",
        "address": "Doğan Taşdelen Bulvarı, Prof. Dr. Ahmet Taner Kışlalı Mahallesi, Çayyolu, Çankaya, Ankara",
        "latitude": 39.8818721,
        "longitude": 32.6859901,
        "prices": (Decimal("115"), Decimal("140"), Decimal("160"), Decimal("130"), Decimal("170")),
    },
]

MENU = [
    ("Espresso", "Tek shot espresso kahve"),
    ("Americano", "Espresso ve sıcak su"),
    ("Cappuccino", "Espresso, süt ve süt köpüğü"),
    ("Türk Kahvesi", "Geleneksel Türk kahvesi"),
    ("Latte", "Espresso ve süt"),
]


def upsert_shop(session: Session, shop_data: ShopSeedData) -> Shop:
    shop = session.scalar(select(Shop).where(Shop.name == shop_data["name"]))
    if shop is None:
        shop = Shop(
            name=shop_data["name"],
            address=shop_data["address"],
            latitude=shop_data["latitude"],
            longitude=shop_data["longitude"],
        )
        session.add(shop)
        session.flush()
    else:
        shop.address = shop_data["address"]
        shop.latitude = shop_data["latitude"]
        shop.longitude = shop_data["longitude"]

    return shop


def upsert_products(session: Session, shop: Shop, prices: tuple[Decimal, ...]) -> None:
    for (name, description), price in zip(MENU, prices, strict=True):
        product = session.scalar(
            select(Product).where(Product.shop_id == shop.id, Product.name == name)
        )
        if product is None:
            product = Product(shop_id=shop.id, name=name, description=description, price=price)
            session.add(product)
        else:
            product.description = description
            product.price = price


def seed_data() -> None:
    Base.metadata.create_all(bind=engine)
    now = datetime.now(UTC)

    with SessionLocal() as session, session.begin():
        for shop_data in SHOPS:
            shop = upsert_shop(session, shop_data)
            upsert_products(session, shop, shop_data["prices"])

        user = session.scalar(
            select(User).where(User.phone_number == TEST_PHONE_NUMBER)
        )
        if user is None:
            user = User(
                phone_number=TEST_PHONE_NUMBER,
                full_name=TEST_USER_NAME,
                role="CUSTOMER",
            )
            session.add(user)
            session.flush()
        else:
            user.full_name = TEST_USER_NAME

        subscription = session.scalar(
            select(Subscription)
            .where(
                Subscription.user_id == user.id,
                Subscription.plan_type == TEST_PLAN,
            )
            .order_by(Subscription.id.desc())
        )
        if subscription is None:
            subscription = Subscription(user_id=user.id, plan_type=TEST_PLAN)
            session.add(subscription)

        subscription.status = "ACTIVE"
        subscription.remaining_credits = TEST_CREDITS
        subscription.started_at = now
        subscription.expires_at = now + timedelta(days=30)

    print(f"Seed verisi hazır: {len(SHOPS)} dükkân, her dükkânda {len(MENU)} ürün.")
    print(f"Test telefonu: {TEST_PHONE_NUMBER} (OTP: 1234)")
    print(f"Abonelik: {TEST_PLAN}, {TEST_CREDITS} kahve hakkı, 30 gün geçerli.")


if __name__ == "__main__":
    seed_data()
