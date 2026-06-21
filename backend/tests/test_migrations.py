from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_creates_commerce_tables(tmp_path) -> None:
    database_path = tmp_path / "migration.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    table_names = set(inspect(engine).get_table_names())
    engine.dispose()

    assert {
        "users",
        "addresses",
        "categories",
        "stores",
        "products",
        "inventory",
        "carts",
        "cart_items",
        "orders",
        "order_items",
        "auth_otp_codes",
        "order_handoff_verifications",
        "support_tickets",
    }.issubset(table_names)
