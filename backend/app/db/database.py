from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker

from app.models import Base

DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parents[2] / 'kahvecell.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection: sqlite3.Connection,
    _connection_record: object,
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    shop_columns = {column["name"] for column in inspect(engine).get_columns("shops")}
    order_columns = {column["name"] for column in inspect(engine).get_columns("orders")}

    with engine.begin() as connection:
        if "profile_complete" not in user_columns:
            connection.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN profile_complete BOOLEAN NOT NULL DEFAULT 0"
            )
        if "coffee_preferences" not in user_columns:
            connection.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN coffee_preferences JSON NOT NULL DEFAULT '[]'"
            )
        if "allergens" not in user_columns:
            connection.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN allergens JSON NOT NULL DEFAULT '[]'"
            )
        connection.exec_driver_sql(
            "UPDATE users SET profile_complete = 1 "
            "WHERE TRIM(full_name) != '' AND profile_complete = 0"
        )
        if "owner_user_id" not in shop_columns:
            connection.exec_driver_sql(
                "ALTER TABLE shops ADD COLUMN owner_user_id INTEGER "
                "REFERENCES users(id) ON DELETE SET NULL"
            )
        if "qr_order_id" not in order_columns:
            connection.exec_driver_sql(
                "ALTER TABLE orders ADD COLUMN qr_order_id VARCHAR(36)"
            )
        if "qr_signature" not in order_columns:
            connection.exec_driver_sql(
                "ALTER TABLE orders ADD COLUMN qr_signature VARCHAR(64)"
            )
        if "delivered_at" not in order_columns:
            connection.exec_driver_sql(
                "ALTER TABLE orders ADD COLUMN delivered_at DATETIME"
            )
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_qr_order_id "
            "ON orders (qr_order_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_shops_owner_user_id "
            "ON shops (owner_user_id)"
        )
