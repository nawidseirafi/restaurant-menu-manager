from pathlib import Path

import pytest

from app.database.db import create_session_factory
from app.database.seed import seed_demo_data


@pytest.fixture()
def session(tmp_path: Path):
    session_factory = create_session_factory(tmp_path / "test_menu.db")
    db_session = session_factory()
    seed_demo_data(db_session)
    db_session.commit()
    try:
        yield db_session
    finally:
        db_session.close()
