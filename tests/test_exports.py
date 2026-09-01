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

    session_factory = create_session_factory(tmp_path / "imported.db")
    imported_session = session_factory()
    try:
        seed_demo_data(imported_session)
        imported_session.commit()
        JsonService().import_menu(imported_session, target)
        exported_again = tmp_path / "menu_again.json"
        JsonService().export_menu(imported_session, exported_again)
        assert "Burrito Pollo" in exported_again.read_text(encoding="utf-8")
    finally:
        imported_session.close()


def test_html_export(session, tmp_path: Path):
    output = HtmlExporter().export(session, tmp_path / "html")
    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "TacoMex" in html
    assert "Nachos con Queso" in html
    assert "Meine Auswahl" in html
    assert "data-item-id=" in html
    assert (tmp_path / "html" / "assets" / "style.css").exists()
    assert (tmp_path / "html" / "assets" / "menu.js").exists()


def test_qr_code_export(session, tmp_path: Path):
    png = QrExporter().export_png("https://menu.tacomex.de", tmp_path / "qr.png")
    svg = QrExporter().export_svg("https://menu.tacomex.de", tmp_path / "qr.svg")
    print_html = QrExporter().export_print_html(
        "https://menu.tacomex.de", tmp_path / "qr-print.html", "TacoMex"
    )
    assert png.exists()
    assert svg.exists()
    assert print_html.exists()
