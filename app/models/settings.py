from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    restaurant_name: Mapped[str] = mapped_column(String(160), default="TacoMex")
    subtitle: Mapped[str | None] = mapped_column(String(255), default="Mexican Kitchen & Bar")
    website_url: Mapped[str | None] = mapped_column(String(500), default="https://tacomex.de")
    menu_url: Mapped[str | None] = mapped_column(String(500), default="https://www.tacomex.de/menu")
    address: Mapped[str | None] = mapped_column(Text, default="")
    phone: Mapped[str | None] = mapped_column(String(80), default="")
    currency: Mapped[str] = mapped_column(String(8), default="EUR")
    logo_path: Mapped[str | None] = mapped_column(String(500))
    default_pdf_template: Mapped[str] = mapped_column(String(80), default="modern_dark")
    default_html_template: Mapped[str] = mapped_column(String(80), default="default")
