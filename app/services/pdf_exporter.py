from __future__ import annotations

import base64
import io
import mimetypes
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.services.export_context import build_menu_context


class PdfExporter:
    def __init__(self, templates_dir: Path | None = None):
        root = Path(__file__).resolve().parents[1]
        self.templates_dir = templates_dir or root / "templates" / "pdf"

    _EXTRA_MIME_TYPES = {
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
    }

    @classmethod
    def _file_data_uri(cls, path: Path) -> str:
        if not path.exists() or not path.is_file():
            return ""
        mime = cls._EXTRA_MIME_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    @staticmethod
    def _qr_data_uri(url: str | None) -> str:
        if not url:
            return ""
        import qrcode

        image = qrcode.make(url)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def render_html(self, session: Session, template_name: str = "modern_dark") -> str:
        template_dir = self.templates_dir / template_name
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        context = build_menu_context(session, active_only=True)
        settings = context["settings"]
        assets_dir = template_dir / "assets"
        cocktail_categories = [
            category
            for category in context["categories"]
            if category.type.value == "cocktails"
        ]
        context.update(
            {
                "asset_data": lambda name: self._file_data_uri(assets_dir / name),
                "cocktail_categories": cocktail_categories,
                "qr_data_uri": self._qr_data_uri(settings.menu_url),
            }
        )
        return env.get_template("menu.html.j2").render(**context)

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
                display_header_footer=False,
            )
            await browser.close()
        return target_pdf
