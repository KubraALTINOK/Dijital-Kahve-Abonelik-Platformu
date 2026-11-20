"""Local-only helper for bootstrapping or changing a user's role."""

import argparse

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models import User
from app.schemas.user import UserRole


def main() -> None:
    parser = argparse.ArgumentParser(description="Set a KahveCell user's role.")
    parser.add_argument("phone_number", help="Verified user's E.164 phone number")
    parser.add_argument("role", choices=[role.value for role in UserRole])
    arguments = parser.parse_args()

    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(User.phone_number == arguments.phone_number)
        )
        if user is None:
            parser.error("Bu telefon numarasıyla kayıtlı kullanıcı bulunamadı.")
        user.role = arguments.role
        session.commit()
        print(f"{user.phone_number} kullanıcısının rolü {user.role} yapıldı.")


if __name__ == "__main__":
    main()
