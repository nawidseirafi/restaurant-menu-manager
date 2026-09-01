from __future__ import annotations

from pathlib import Path

import qrcode
import qrcode.image.svg


class QrExporter:
    def export_png(self, url: str, target: Path) -> Path:
        self._validate_url(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        image = qrcode.make(url)
        image.save(target)
        return target

    def export_svg(self, url: str, target: Path) -> Path:
        self._validate_url(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        factory = qrcode.image.svg.SvgPathImage
        image = qrcode.make(url, image_factory=factory)
        image.save(target)
        return target

    def export_print_html(self, url: str, target: Path, restaurant_name: str = "TacoMex") -> Path:
        self._validate_url(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        svg_target = target.with_suffix(".svg")
        self.export_svg(url, svg_target)
        target.write_text(
            f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>QR Speisekarte</title>
<style>
@page {{ size: A6; margin: 12mm; }}
body {{ font-family: Arial, sans-serif; text-align: center; color: #231814; }}
.brand {{ font-size: 24px; font-weight: 800; margin-top: 8mm; }}
.label {{ font-size: 18px; margin: 8mm 0 4mm; }}
img {{ width: 58mm; height: 58mm; }}
.hint {{ margin-top: 5mm; font-size: 13px; }}
</style></head><body>
<div class="brand">{restaurant_name}</div>
<div class="label">Speisekarte</div>
<img src="{svg_target.name}" alt="QR-Code">
<div class="hint">Scannen &amp; Menue ansehen</div>
</body></html>""",
            encoding="utf-8",
        )
        return target

    def _validate_url(self, url: str) -> None:
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError("Bitte eine gueltige URL mit http:// oder https:// verwenden.")
