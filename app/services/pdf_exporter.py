from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.services.export_context import build_menu_context


class PdfExporter:
    def __init__(self, templates_dir: Path | None = None):
        root = Path(__file__).resolve().parents[1]
        self.templates_dir = templates_dir or root / "templates" / "pdf"

    async def export(self, session: Session, target_pdf: Path, template_name: str = "modern_dark") -> Path:
        from playwright.async_api import async_playwright

        template_dir = self.templates_dir / template_name
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        html = env.get_template("menu.html.j2").render(**build_menu_context(session, active_only=True))
        target_pdf.parent.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            await page.pdf(
                path=str(target_pdf),
                format="A4",
                print_background=True,
                margin={"top": "12mm", "right": "10mm", "bottom": "14mm", "left": "10mm"},
            )
            await browser.close()
        return target_pdf
