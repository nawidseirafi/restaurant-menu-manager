from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, CategoryType, MenuItem, Settings


DEMO_MENU = [
    ("Vorspeisen & Nachos", CategoryType.food, [
        ("Nachos con Queso", "Tortilla Chips mit warmer Kaesesauce und Salsa.", "6.90", False, False, 1),
        ("Nachos con Chili", "Tortilla Chips mit Chili con Carne, Kaese und Jalapenos.", "8.90", False, False, 2),
        ("Guacamole", "Frische Avocadocreme mit Limette, Koriander und Tortilla Chips.", "5.90", True, True, 0),
        ("Quesadillas", "Gegrillte Weizentortillas mit Kaese, Paprika und Salsa.", "7.90", True, False, 1),
    ]),
    ("Burritos", CategoryType.food, [
        ("Burrito Pollo", "Gefuellte Weizentortilla mit Haehnchen, Reis, Bohnen und Pico de Gallo.", "11.90", False, False, 1),
        ("Burrito Carne", "Mit Rindfleisch, Bohnen, Reis, Kaese und rauchiger Salsa.", "12.90", False, False, 2),
        ("Burrito Vegetariano", "Mit Grillgemuese, Bohnen, Reis, Guacamole und Salsa Verde.", "10.90", True, True, 1),
    ]),
    ("Fajitas", CategoryType.food, [
        ("Fajitas de Pollo", "Haehnchenstreifen mit Paprika, Zwiebeln und warmen Tortillas.", "15.90", False, False, 1),
        ("Fajitas de Res", "Rindfleischstreifen mit Grillgemuese, Salsa und Sour Cream.", "17.90", False, False, 1),
        ("Fajitas Mixtas", "Haehnchen und Rind mit Paprika, Zwiebeln und Dips.", "18.90", False, False, 2),
    ]),
    ("Burger", CategoryType.food, [
        ("TacoMex Burger", "Rindfleischpatty mit Cheddar, Jalapenos, Salsa Roja und Pommes.", "13.90", False, False, 2),
        ("Chicken Burger", "Knuspriges Haehnchen, Chipotle Mayo, Salat und Pommes.", "12.90", False, False, 1),
    ]),
    ("Cocktails", CategoryType.cocktails, [
        ("Mojito", "Rum, Limette, Minze, Rohrzucker und Soda.", "8.50", False, True, 0),
        ("Caipirinha", "Cachaca, Limette und Rohrzucker.", "8.50", False, True, 0),
        ("Margarita", "Tequila, Triple Sec und Limettensaft.", "8.90", False, True, 0),
        ("Pina Colada", "Rum, Ananas, Kokos und Sahne.", "8.90", False, False, 0),
    ]),
]


def seed_demo_data(session: Session) -> None:
    if session.scalar(select(Category.id).limit(1)):
        return

    session.add(Settings(id=1))
    order_number = 200
    for category_index, (name, category_type, items) in enumerate(DEMO_MENU, start=1):
        category = Category(
            name=name,
            description=None,
            sort_order=category_index,
            active=True,
            type=category_type,
        )
        session.add(category)
        session.flush()
        for item_index, (item_name, description, price, vegetarian, vegan, spicy) in enumerate(items, start=1):
            item_order_number = None
            if category_type not in {CategoryType.drinks, CategoryType.cocktails}:
                item_order_number = order_number
                order_number += 1
            session.add(
                MenuItem(
                    category_id=category.id,
                    order_number=item_order_number,
                    name=item_name,
                    description=description,
                    price=Decimal(price),
                    sort_order=item_index,
                    active=True,
                    vegetarian=vegetarian,
                    vegan=vegan,
                    spicy_level=spicy,
                )
            )
