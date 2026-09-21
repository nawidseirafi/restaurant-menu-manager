from decimal import Decimal

from app.database.repositories import MenuRepository
from app.models import Category, CategoryType, MenuItem


def test_database_creation_with_demo_data(session):
    repo = MenuRepository(session)
    categories = repo.list_categories()
    assert categories
    assert any(category.name == "Burritos" for category in categories)


def test_obsolete_tequila_note_is_removed_from_existing_database(tmp_path):
    from app.database.db import create_session_factory
    from app.services.html_exporter import HtmlExporter

    path = tmp_path / "legacy_note.db"
    factory = create_session_factory(path)
    with factory() as session:
        session.add_all([
            Category(name="Tequila Añejo", description="Preise laut Karte pro 2 cl."),
            Category(name="Andere Kategorie", description="Eigener Hinweis"),
        ])
        session.commit()
    factory.kw["bind"].dispose()

    for _ in range(2):
        factory = create_session_factory(path)
        with factory() as session:
            categories = {c.name: c for c in MenuRepository(session).list_categories()}
            assert categories["Tequila Añejo"].description == ""
            assert categories["Andere Kategorie"].description == "Eigener Hinweis"
            html = HtmlExporter().export(session, tmp_path / "html").read_text()
            assert "Preise laut Karte pro 2 cl." not in html
            assert "Eigener Hinweis" in html
        factory.kw["bind"].dispose()

    with factory() as session:
        categories = {c.name: c for c in MenuRepository(session).list_categories()}
        categories["Tequila Añejo"].description = "Individueller Hinweis"
        session.commit()
    factory.kw["bind"].dispose()
    factory = create_session_factory(path)
    with factory() as session:
        categories = {c.name: c for c in MenuRepository(session).list_categories()}
        assert categories["Tequila Añejo"].description == "Individueller Hinweis"
    factory.kw["bind"].dispose()


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
            order_number=999,
            name="Taco Test",
            description="Testbeschreibung",
            price=Decimal("9.50"),
            sort_order=99,
            active=True,
        )
    )
    assert item.id is not None
    assert repo.get_item(item.id).price == Decimal("9.50")
    assert repo.get_item(item.id).order_number == 999


def test_change_price(session):
    repo = MenuRepository(session)
    item = repo.list_items()[0]
    repo.update_item_price(item.id, Decimal("12.30"))
    assert repo.get_item(item.id).price == Decimal("12.30")


def test_demo_cocktails_do_not_require_order_numbers(session):
    repo = MenuRepository(session)
    cocktail_category = next(category for category in repo.list_categories() if category.type == CategoryType.cocktails)
    cocktail = repo.list_items(cocktail_category.id)[0]
    assert cocktail.order_number is None


def test_settings_menu_url_defaults_and_migrates(session):
    from app.database.repositories import MenuRepository

    repo = MenuRepository(session)
    settings = repo.get_settings()
    assert settings.menu_url == "https://www.tacomex.de/menu"

    settings.menu_url = "https://tacomex.de/menu"
    session.commit()
    migrated = repo.get_settings()
    assert migrated.menu_url == "https://www.tacomex.de/menu"


def test_price_sizes_survive_duplicate_and_independent_price_changes(session):
    repo = MenuRepository(session)
    item = repo.list_items()[0]
    item.price_label = "0,2 l"
    item.price = Decimal("2.90")
    item.second_price_label = "0,3 l"
    item.second_price = Decimal("3.90")
    repo.save_item(item)
    clone = repo.duplicate_item(item.id)
    assert (clone.price_label, clone.second_price_label) == ("0,2 l", "0,3 l")
    repo.update_item_price(item.id, Decimal("4.10"), second=True)
    session.expire_all()
    assert item.price == Decimal("2.90")
    assert item.second_price == Decimal("4.10")
    assert clone.second_price == Decimal("3.90")


def test_old_database_gets_price_label_without_changing_prices(tmp_path):
    import sqlite3
    from app.database.db import create_session_factory

    path = tmp_path / "legacy.db"
    factory = create_session_factory(path)
    factory.kw["bind"].dispose()
    with sqlite3.connect(path) as connection:
        connection.execute("ALTER TABLE menu_items DROP COLUMN price_label")
        connection.execute("INSERT INTO categories (id, name, type, sort_order, active) VALUES (1, 'Getränke', 'drinks', 1, 1)")
        connection.execute("INSERT INTO menu_items (id, category_id, name, price, second_price, sort_order, active, vegetarian, vegan, spicy_level) VALUES (1, 1, 'Cola', 2.9, 3.9, 1, 1, 0, 0, 0)")
    for _ in range(2):
        factory = create_session_factory(path)
        with factory() as session:
            item = session.get(MenuItem, 1)
            assert item.price_label is None
            assert (item.price, item.second_price) == (Decimal('2.90'), Decimal('3.90'))
        factory.kw["bind"].dispose()
