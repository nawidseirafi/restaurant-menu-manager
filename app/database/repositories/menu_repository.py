from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Category, CategoryType, MenuItem, Settings


class ValidationError(ValueError):
    pass


class MenuRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_categories(self, active_only: bool = False) -> list[Category]:
        stmt = select(Category).order_by(Category.sort_order, Category.name)
        if active_only:
            stmt = stmt.where(Category.active.is_(True))
        return list(self.session.scalars(stmt))

    def get_category(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def save_category(self, category: Category) -> Category:
        if not category.name.strip():
            raise ValidationError("Kategorie benoetigt einen Namen.")
        self.session.add(category)
        self.session.commit()
        return category

    def delete_category(self, category_id: int) -> None:
        category = self.get_category(category_id)
        if category:
            self.session.delete(category)
            self.session.commit()

    def list_items(self, category_id: int | None = None, active_only: bool = False) -> list[MenuItem]:
        stmt = select(MenuItem).order_by(MenuItem.sort_order, MenuItem.name)
        if category_id is not None:
            stmt = stmt.where(MenuItem.category_id == category_id)
        if active_only:
            stmt = stmt.where(MenuItem.active.is_(True))
        return list(self.session.scalars(stmt))

    def get_item(self, item_id: int) -> MenuItem | None:
        return self.session.get(MenuItem, item_id)

    def save_item(self, item: MenuItem) -> MenuItem:
        self._validate_item(item)
        self.session.add(item)
        self.session.commit()
        return item

    def duplicate_item(self, item_id: int) -> MenuItem:
        item = self.get_item(item_id)
        if not item:
            raise ValidationError("Gericht wurde nicht gefunden.")
        clone = MenuItem(
            category_id=item.category_id,
            name=f"{item.name} Kopie",
            description=item.description,
            price=item.price,
            second_price=item.second_price,
            second_price_label=item.second_price_label,
            sort_order=item.sort_order + 1,
            active=item.active,
            vegetarian=item.vegetarian,
            vegan=item.vegan,
            spicy_level=item.spicy_level,
            allergens=item.allergens,
            additives=item.additives,
            image_path=item.image_path,
            notes=item.notes,
        )
        return self.save_item(clone)

    def delete_item(self, item_id: int) -> None:
        item = self.get_item(item_id)
        if item:
            self.session.delete(item)
            self.session.commit()

    def update_item_price(self, item_id: int, price: Decimal) -> None:
        price = Decimal(str(price)).quantize(Decimal("0.01"))
        if price < 0:
            raise ValidationError("Preis darf nicht negativ sein.")
        item = self.get_item(item_id)
        if not item:
            raise ValidationError("Gericht wurde nicht gefunden.")
        item.price = price
        self.session.commit()

    def reorder_category(self, category_id: int, direction: int) -> None:
        categories = self.list_categories()
        self._move_ordered(categories, category_id, direction)

    def reorder_item(self, item_id: int, direction: int) -> None:
        item = self.get_item(item_id)
        if not item:
            return
        items = self.list_items(item.category_id)
        self._move_ordered(items, item_id, direction)

    def set_category_order(self, category_ids: list[int]) -> None:
        categories = {category.id: category for category in self.list_categories()}
        for sort_order, category_id in enumerate(category_ids, start=1):
            category = categories.get(category_id)
            if category:
                category.sort_order = sort_order
        self.session.commit()

    def set_item_order(self, category_id: int, item_ids: list[int]) -> None:
        items = {item.id: item for item in self.list_items(category_id)}
        for sort_order, item_id in enumerate(item_ids, start=1):
            item = items.get(item_id)
            if item:
                item.sort_order = sort_order
        self.session.commit()

    def get_settings(self) -> Settings:
        settings = self.session.get(Settings, 1)
        if not settings:
            settings = Settings(id=1)
            self.session.add(settings)
            self.session.commit()
        return settings

    def menu_tree(self, active_only: bool = True) -> list[Category]:
        stmt = (
            select(Category)
            .options(selectinload(Category.items))
            .order_by(Category.sort_order, Category.name)
        )
        if active_only:
            stmt = stmt.where(Category.active.is_(True))
        categories = list(self.session.scalars(stmt))
        if active_only:
            for category in categories:
                category.items = sorted(
                    [item for item in category.items if item.active],
                    key=lambda item: (item.sort_order, item.name),
                )
        return categories

    def _move_ordered(self, rows: list[Category] | list[MenuItem], row_id: int, direction: int) -> None:
        index = next((idx for idx, row in enumerate(rows) if row.id == row_id), None)
        if index is None:
            return
        new_index = max(0, min(len(rows) - 1, index + direction))
        if new_index == index:
            return
        rows[index], rows[new_index] = rows[new_index], rows[index]
        for sort_order, row in enumerate(rows, start=1):
            row.sort_order = sort_order
        self.session.commit()

    def _validate_item(self, item: MenuItem) -> None:
        if not item.name.strip():
            raise ValidationError("Gericht benoetigt einen Namen.")
        if not item.category_id or not self.get_category(item.category_id):
            raise ValidationError("Bitte eine gueltige Kategorie auswaehlen.")
        try:
            item.price = Decimal(str(item.price)).quantize(Decimal("0.01"))
            if item.second_price is not None:
                item.second_price = Decimal(str(item.second_price)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError):
            raise ValidationError("Bitte einen gueltigen Preis eingeben.") from None
        if item.price < 0:
            raise ValidationError("Preis darf nicht negativ sein.")
