from decimal import Decimal

from app.database.repositories import MenuRepository
from app.models import Category, CategoryType, MenuItem


def test_database_creation_with_demo_data(session):
    repo = MenuRepository(session)
    categories = repo.list_categories()
    assert categories
    assert any(category.name == "Burritos" for category in categories)


def test_create_category(session):
    repo = MenuRepository(session)
    category = repo.save_category(
        Category(name="Desserts", sort_order=99, active=True, type=CategoryType.dessert)
    )
    assert category.id is not None
    assert repo.get_category(category.id).name == "Desserts"


def test_create_menu_item(session):
    repo = MenuRepository(session)
    category = repo.list_categories()[0]
    item = repo.save_item(
        MenuItem(
            category_id=category.id,
            name="Taco Test",
            description="Testbeschreibung",
            price=Decimal("9.50"),
            sort_order=99,
            active=True,
        )
    )
    assert item.id is not None
    assert repo.get_item(item.id).price == Decimal("9.50")


def test_change_price(session):
    repo = MenuRepository(session)
    item = repo.list_items()[0]
    repo.update_item_price(item.id, Decimal("12.30"))
    assert repo.get_item(item.id).price == Decimal("12.30")


def test_settings_menu_url_defaults_and_migrates(session):
    from app.database.repositories import MenuRepository

    repo = MenuRepository(session)
    settings = repo.get_settings()
    assert settings.menu_url == "https://www.tacomex.de/menu"

    settings.menu_url = "https://menu.tacomex.de"
    session.commit()
    migrated = repo.get_settings()
    assert migrated.menu_url == "https://www.tacomex.de/menu"
