from app.database.db import create_session_factory
from app.database.seed import seed_demo_data
from app.gui.main_window import run_app
from app.logging_config import configure_logging


def main() -> int:
    configure_logging()
    session_factory = create_session_factory()
    session = session_factory()
    try:
        seed_demo_data(session)
        session.commit()
    finally:
        session.close()
    return run_app(session_factory)


if __name__ == "__main__":
    raise SystemExit(main())
