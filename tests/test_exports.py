from pathlib import Path

from app.database.db import create_session_factory
from app.database.seed import seed_demo_data
from app.services.html_exporter import HtmlExporter
from app.services.json_service import JsonService
from app.services.qr_exporter import QrExporter


def test_json_export_import(session, tmp_path: Path):
    target = tmp_path / "menu.json"
    JsonService().export_menu(session, target)
    assert target.exists()
    assert "Nachos con Queso" in target.read_text(encoding="utf-8")
    assert '"order_number": 200' in target.read_text(encoding="utf-8")

    session_factory = create_session_factory(tmp_path / "imported.db")
    imported_session = session_factory()
    try:
        seed_demo_data(imported_session)
        imported_session.commit()
        JsonService().import_menu(imported_session, target)
        exported_again = tmp_path / "menu_again.json"
        JsonService().export_menu(imported_session, exported_again)
        assert "Burrito Pollo" in exported_again.read_text(encoding="utf-8")
        assert '"order_number": 200' in exported_again.read_text(encoding="utf-8")
    finally:
        imported_session.close()


def test_html_export(session, tmp_path: Path):
    output = HtmlExporter().export(session, tmp_path / "html")
    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "TacoMex" in html
    assert "Nachos con Queso" in html
    assert '<span class="order-number">200.</span>Nachos con Queso' in html
    assert 'data-order-number="200"' in html
    assert "Meine Auswahl" in html
    assert "data-item-id=" in html
    assert (tmp_path / "html" / "assets" / "style.css").exists()
    assert (tmp_path / "html" / "assets" / "menu.js").exists()


def test_qr_code_export(session, tmp_path: Path):
    png = QrExporter().export_png("https://tacomex.de/menu", tmp_path / "qr.png")
    svg = QrExporter().export_svg("https://tacomex.de/menu", tmp_path / "qr.svg")
    print_html = QrExporter().export_print_html(
        "https://tacomex.de/menu", tmp_path / "qr-print.html", "TacoMex"
    )
    assert png.exists()
    assert svg.exists()
    assert print_html.exists()


def test_size_prices_round_trip_and_html_export(session, tmp_path):
    from decimal import Decimal
    from app.database.repositories import MenuRepository
    from app.services.pdf_exporter import PdfExporter

    repo = MenuRepository(session)
    item = repo.list_items()[0]
    name = item.name
    item.price_label = "0,2 l"
    item.price = Decimal("2.90")
    item.second_price_label = "0,3 l"
    item.second_price = Decimal("3.90")
    repo.save_item(item)
    service = JsonService()
    target = service.export_menu(session, tmp_path / 'sizes.json')
    service.import_menu(session, target)
    restored = next(item for item in repo.list_items() if item.name == name)
    assert (restored.price_label, restored.second_price_label) == ('0,2 l', '0,3 l')
    assert (restored.price, restored.second_price) == (Decimal('2.90'), Decimal('3.90'))
    html = HtmlExporter().export(session, tmp_path / 'html').read_text()
    assert 'data-price-label="0,2 l"' in html
    assert 'data-second-price-label="0,3 l"' in html
    assert 'data-price-cents="290"' in html
    assert 'data-second-price-cents="390"' in html
    assert 'class="price-size">0,2 l</span>' in html
    pdf_html = PdfExporter().render_html(session)
    assert '0,2 l · 2,90 €' in pdf_html
    assert '0,3 l' in pdf_html
