from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.services.export_context import build_menu_context


class PdfExporter:
    def __init__(self, templates_dir: Path | None = None):
        root = Path(__file__).resolve().parents[1]
        self.templates_dir = templates_dir or root / "templates" / "pdf"

    def render_html(self, session: Session, template_name: str = "modern_dark") -> str:
        template_dir = self.templates_dir / template_name
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        return env.get_template("menu.html.j2").render(**build_menu_context(session, active_only=True))

    async def export(self, session: Session, target_pdf: Path, template_name: str = "modern_dark") -> Path:
        from playwright.async_api import async_playwright

        html = self.render_html(session, template_name)
        target_pdf.parent.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            await page.pdf(
                path=str(target_pdf),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=True,
                header_template="""
                    <div style="width:100%; margin:0 13mm; padding-bottom:3mm; border-bottom:1px solid rgba(179,38,30,.65); color:#f9f1df; font-family:Arial, sans-serif; font-size:8px; font-weight:700; display:flex; justify-content:space-between;">
                        <span><b>TACO<span style="color:#df3a2e;">MEX</span></b> · SPEISEKARTE</span>
                        <span>Mexican Restaurant · Tapas & Cocktails</span>
                    </div>
                """,
                footer_template="""
                    <div style="width:100%; margin:0 13mm; padding-top:2mm; border-top:1px solid rgba(215,168,74,.5); color:#d7a84a; font-family:Arial, sans-serif; font-size:8px; font-weight:700; display:flex; justify-content:space-between;">
                        <span>tacomex.de</span>
                        <span>Seite <span class="pageNumber"></span></span>
                    </div>
                """,
            )
            await browser.close()
        return target_pdf
