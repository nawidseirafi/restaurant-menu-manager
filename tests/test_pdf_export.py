from decimal import Decimal

from app.database.repositories import MenuRepository
from app.models import MenuItem
from app.services.pdf_exporter import PdfExporter


def test_pdf_template_renders_full_active_menu(session):
    repo = MenuRepository(session)
    html = PdfExporter().render_html(session)

    for category in repo.list_categories(active_only=True):
        assert category.name in html
        for item in repo.list_items(category.id, active_only=True):
            assert item.name in html
            assert f"{item.price:.2f}".replace(".", ",") in html


def test_pdf_template_renders_second_price(session):
    repo = MenuRepository(session)
    item = repo.list_items()[0]
    item.second_price = Decimal("19.90")
    item.second_price_label = "2 Pers."
    session.commit()

    html = PdfExporter().render_html(session)

    assert "2 Pers." in html
    assert "19,90" in html


def test_pdf_template_uses_branded_cover_and_section_page_breaks(session):
    html = PdfExporter().render_html(session)

    assert 'class="cover"' in html
    assert 'class="menu-page food-page start-page"' in html
    assert 'class="menu-page burger-page start-page"' in html
    assert 'class="menu-page drinks-page start-page"' in html
    assert 'class="menu-page cocktails-page cocktails-page-one start-page"' in html
    assert 'class="menu-page cocktails-page cocktails-page-two start-page"' in html
    assert 'Holz-Hintergrund.png' not in html  # asset is embedded as a data URI
    assert 'Cocktail-1.png' not in html  # asset is embedded as a data URI
    assert 'Cocktail-2.png' not in html  # asset is embedded as a data URI
    assert 'original_wood.jpg' not in html
    assert 'original_cover.png' not in html  # asset is embedded as a data URI
    assert 'data:image/png;base64,' in html
    assert 'data:image/jpeg;base64,' not in html
    assert 'class="photo' not in html
    assert "TacoMex Speisen und Getränke" in html
    assert "cover.png" not in html
    assert "columns:2" not in html
    assert 'cover-qr' not in html
    assert '<h1 class="page-title">Getränke</h1>' in html
    assert '<h1 class="page-title">Cocktails</h1>' in html
    assert 'break-before:page' in html
    assert 'page-break-before' not in html
    assert 'height: 100vh' not in html
    assert 'class="outro"' not in html

def test_pdf_template_handles_long_descriptions(session):
    repo = MenuRepository(session)
    category = repo.list_categories(active_only=True)[0]
    repo.save_item(
        MenuItem(
            category_id=category.id,
            name="Lange Beschreibung Test",
            description=" ".join(["Sehr ausfuehrliche Beschreibung"] * 80),
            price=Decimal("12.40"),
            sort_order=999,
            active=True,
        )
    )

    html = PdfExporter().render_html(session)

    assert "Lange Beschreibung Test" in html
    assert "Sehr ausfuehrliche Beschreibung" in html
