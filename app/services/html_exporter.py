from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.services.export_context import build_menu_context


class HtmlExporter:
    def __init__(self, templates_dir: Path | None = None):
        root = Path(__file__).resolve().parents[1]
        self.templates_dir = templates_dir or root / "templates" / "html"

    def export(self, session: Session, target_dir: Path, template_name: str = "default") -> Path:
        template_dir = self.templates_dir / template_name
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        context = build_menu_context(session, active_only=True)
        html = env.get_template("index.html.j2").render(**context)
        target_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = target_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        (target_dir / "index.html").write_text(html, encoding="utf-8")
        for asset in ["style.css", "menu.js"]:
            source = template_dir / asset
            if source.exists():
                shutil.copyfile(source, assets_dir / asset)
        return target_dir / "index.html"
