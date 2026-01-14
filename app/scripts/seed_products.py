import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from models.product import Product


# -----------------------------
# Helpers
# -----------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return float(
        str(value)
        .replace("₹", "")
        .replace("%", "")
        .replace(",", "")
        .strip()
    )


# -----------------------------
# Core mapper
# -----------------------------
def map_to_product(item, main_category, sub_category=None):
    return Product(
        name=item.get("name"),
        category=main_category,
        sub_category=sub_category or item.get("medicine_type") or item.get("category"),
        brand=item.get("brand"),

        price=clean_price(
            item.get("final_price") or item.get("priceNumeric")
        ),
        original_price=clean_price(
            item.get("cost") or item.get("originalPriceNumeric")
        ),
        discount=clean_price(item.get("discount")),

        stock=item.get("stock", 0),

        image=item.get("images") or item.get("image"),
        description=item.get("description"),
        ingredients=(
            ", ".join(item["ingredients"])
            if isinstance(item.get("ingredients"), list)
            else item.get("ingredients")
        ),
        how_to_use=item.get("howToUse")
            or item.get("usage_instruction"),
        warnings=item.get("warnings"),

        # EVERYTHING ELSE
        extra_data={
            k: v for k, v in item.items()
            if k not in {
                "name", "brand", "stock", "images", "image",
                "description", "ingredients", "howToUse",
                "usage_instruction", "warnings",
                "final_price", "priceNumeric",
                "cost", "originalPriceNumeric",
                "discount", "medicine_type", "category"
            }
        }
    )


# -----------------------------
# Seeders
# -----------------------------
async def seed_livercare(db: AsyncSession):
    data = load_json("data/LiverCare.json")["product"]

    for section, items in data.items():
        for item in items:
            db.add(map_to_product(
                item,
                main_category="LiverCare",
                sub_category=section
            ))


async def seed_covid(db: AsyncSession):
    data = load_json("data/covidesentials.json")

    for item in data:
        db.add(map_to_product(
            item,
            main_category="Covid Essentials",
            sub_category=item.get("category")
        ))


async def seed_babycare(db: AsyncSession):
    data = load_json("data/babycare.json")

    for item in data:
        db.add(map_to_product(
            item,
            main_category="Baby Care",
            sub_category=item.get("category")
        ))


# -----------------------------
# Runner
# -----------------------------
async def main():
    async with AsyncSessionLocal() as db:
        await seed_livercare(db)
        await seed_covid(db)
        await seed_babycare(db)

        await db.commit()
        print("✅ Product seeding completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
