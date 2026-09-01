from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.database.repositories import MenuRepository
from app.models import Category, CategoryType, MenuItem


class JsonService:
    def export_menu(self, session: Session, target: Path) -> Path:
        repo = MenuRepository(session)
        settings = repo.get_settings()
        data = {
            "settings": {
                "restaurant_name": settings.restaurant_name,
                "subtitle": settings.subtitle,
                "website_url": settings.website_url,
                "menu_url": settings.menu_url,
                "address": settings.address,
                "phone": settings.phone,
                "currency": settings.currency,
                "logo_path": settings.logo_path,
                "default_pdf_template": settings.default_pdf_template,
                "default_html_template": settings.default_html_template,
            },
            "categories": [],
        }
        for category in repo.menu_tree(active_only=False):
            data["categories"].append(
                {
                    "name": category.name,
                    "description": category.description,
                    "sort_order": category.sort_order,
                    "active": category.active,
                    "type": category.type.value,
                    "items": [
                        {
                            "name": item.name,
                            "description": item.description,
                            "price": str(item.price),
                            "second_price": str(item.second_price) if item.second_price is not None else None,
                            "second_price_label": item.second_price_label,
                            "sort_order": item.sort_order,
                            "active": item.active,
                            "vegetarian": item.vegetarian,
                            "vegan": item.vegan,
                            "spicy_level": item.spicy_level,
                            "allergens": item.allergens,
                            "additives": item.additives,
                            "image_path": item.image_path,
                            "notes": item.notes,
                        }
                        for item in category.items
                    ],
                }
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def import_menu(self, session: Session, source: Path) -> None:
        data = json.loads(source.read_text(encoding="utf-8"))
        repo = MenuRepository(session)
        settings = repo.get_settings()
        for key, value in data.get("settings", {}).items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        for category in repo.list_categories(active_only=False):
            session.delete(category)
        session.flush()
        for category_data in data.get("categories", []):
            category = Category(
                name=category_data["name"],
                description=category_data.get("description"),
                sort_order=category_data.get("sort_order", 0),
                active=category_data.get("active", True),
                type=CategoryType(category_data.get("type", "food")),
            )
            session.add(category)
            session.flush()
            for item_data in category_data.get("items", []):
                session.add(
                    MenuItem(
                        category_id=category.id,
                        name=item_data["name"],
                        description=item_data.get("description"),
                        price=Decimal(item_data["price"]),
                        second_price=Decimal(item_data["second_price"]) if item_data.get("second_price") else None,
                        second_price_label=item_data.get("second_price_label"),
                        sort_order=item_data.get("sort_order", 0),
                        active=item_data.get("active", True),
                        vegetarian=item_data.get("vegetarian", False),
                        vegan=item_data.get("vegan", False),
                        spicy_level=item_data.get("spicy_level", 0),
                        allergens=item_data.get("allergens"),
                        additives=item_data.get("additives"),
                        image_path=item_data.get("image_path"),
                        notes=item_data.get("notes"),
                    )
                )
        session.commit()
