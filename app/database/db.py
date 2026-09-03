from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "tacomex_menu.db"


class Base(DeclarativeBase):
    pass


def get_database_url(db_path: Path | str | None = None) -> str:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def create_session_factory(db_path: Path | str | None = None) -> sessionmaker[Session]:
    import app.models  # noqa: F401  Ensures models are registered on Base.metadata.

    engine = create_engine(get_database_url(db_path), future=True)
    Base.metadata.create_all(engine)
    _migrate_sqlite_schema(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def _migrate_sqlite_schema(engine) -> None:
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(menu_items)")
        }
        if "order_number" not in columns:
            connection.exec_driver_sql("ALTER TABLE menu_items ADD COLUMN order_number INTEGER")
            connection.execute(
                text(
                    """
                    UPDATE menu_items
                    SET order_number = id + 199
                    WHERE order_number IS NULL
                    """
                )
            )
        connection.execute(
            text(
                """
                UPDATE menu_items
                SET order_number = NULL
                WHERE category_id IN (
                    SELECT id
                    FROM categories
                    WHERE type IN ('drinks', 'cocktails')
                )
                AND order_number = id + 199
                """
            )
        )


def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
