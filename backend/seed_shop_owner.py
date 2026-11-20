"""Create a demo shop-owner account and assign it to CoffeeLab."""

from sqlalchemy import select

from app.db.database import SessionLocal, create_db_and_tables
from app.models import Shop, User

TEST_OWNER_PHONE_NUMBER = "+905550000003"
TEST_OWNER_NAME = "KahveCell Dükkân Test"
TEST_SHOP_NAME = "CoffeeLab"


def seed_shop_owner() -> None:
    create_db_and_tables()
    with SessionLocal() as session, session.begin():
        shop = session.scalar(select(Shop).where(Shop.name == TEST_SHOP_NAME))
        if shop is None:
            raise RuntimeError(f"Test dükkânı bulunamadı: {TEST_SHOP_NAME}")

        user = session.scalar(
            select(User).where(User.phone_number == TEST_OWNER_PHONE_NUMBER)
        )
        if user is None:
            user = User(
                phone_number=TEST_OWNER_PHONE_NUMBER,
                full_name=TEST_OWNER_NAME,
                role="SHOP_OWNER",
                profile_complete=True,
            )
            session.add(user)
            session.flush()
        else:
            user.full_name = TEST_OWNER_NAME
            user.role = "SHOP_OWNER"
            user.profile_complete = True

        if shop.owner_user_id not in (None, user.id):
            raise RuntimeError(
                f"{TEST_SHOP_NAME} başka bir dükkân sahibine atanmış; "
                "atama otomatik değiştirilmedi."
            )
        shop.owner_user_id = user.id

    print(f"Test dükkân sahibi hazır: {TEST_OWNER_PHONE_NUMBER} (OTP: 1234)")
    print(f"Atanan dükkân: {TEST_SHOP_NAME}")


if __name__ == "__main__":
    seed_shop_owner()
