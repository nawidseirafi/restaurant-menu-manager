from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.database.repositories import MenuRepository


def format_price(value: Decimal | None, currency: str = "EUR") -> str:
    if value is None:
        return ""
    suffix = "EUR" if currency != "EUR" else "EUR"
    return f"{Decimal(value):.2f} {suffix}".replace(".", ",")


def build_menu_context(session: Session, active_only: bool = True) -> dict:
    repo = MenuRepository(session)
    settings = repo.get_settings()
    return {
        "settings": settings,
        "categories": repo.menu_tree(active_only=active_only),
        "format_price": lambda value: format_price(value, settings.currency),
    }
