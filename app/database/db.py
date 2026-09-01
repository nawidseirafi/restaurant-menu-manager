from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
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
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


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
