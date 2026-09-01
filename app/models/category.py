import enum

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class CategoryType(str, enum.Enum):
    food = "food"
    drinks = "drinks"
    cocktails = "cocktails"
    dessert = "dessert"
    other = "other"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    type: Mapped[CategoryType] = mapped_column(
        Enum(CategoryType), default=CategoryType.food, nullable=False
    )

    items: Mapped[list["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="MenuItem.sort_order",
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r})"
