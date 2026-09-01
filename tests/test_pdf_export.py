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

    assert "page-break-after: always" not in html
    assert "page-break-before" not in html
    assert ".menu-pages.drinks-start,.menu-pages.cocktails-start{break-before:page}" in html
    assert 'class="menu-pages cocktails-start"' in html
    assert '<div class="section-label">Essen</div>' in html
    assert '<div class="section-label">Getränke</div>' in html
    assert '<div class="section-label">Cocktails</div>' in html
    assert 'class="menu-pages drinks-start"' in html
    assert "break-after: always" not in html
    assert "height: 100vh" not in html
    assert 'class="cover"' in html
    assert 'class="outro"' not in html
    assert "qr_data_uri" not in html  # Jinja value must be rendered, not leaked
    assert "data:image/png;base64," in html
    assert "Facebook" in html
    assert "Instagram" in html
    assert 'class="cover-qr"' in html
    assert 'class="menu-photo"' in html


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
