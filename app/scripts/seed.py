import json
import asyncio
from core.database import AsyncSessionLocal, engine
from models.base import Base
from models.product import Product


# -------------------------------
# Load JSON file
# -------------------------------
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# -------------------------------
# Clean numeric values
# -------------------------------
def clean_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    return float(
        value.replace("₹", "")
             .replace("%", "")
             .replace(",", "")
             .strip()
    )


# -------------------------------
# Map JSON item -> Product
# -------------------------------
def map_product(item, category):
    return Product(
        name=item.get("name"),
        category=category,

        sub_category=(
            item.get("category")
            or item.get("medicine_type")
            or item.get("product_type")
        ),

        brand=(
            item.get("brand")
            or item.get("manufacturer")
            or item.get("company_name")
        ),

        price=clean_number(
            item.get("priceNumeric")
            or item.get("price")
            or item.get("cost")
        ),

        original_price=clean_number(
            item.get("originalPriceNumeric")
            or item.get("originalPrice")
        ),

        discount=clean_number(
            item.get("discount")
            or item.get("savings")
        ),

        # ✅ Stock column
        stock=item.get("stock") or 0,

        image=item.get("image") or item.get("images"),
        description=item.get("description"),

        ingredients=(
            ", ".join(item.get("ingredients"))
            if isinstance(item.get("ingredients"), list)
            else item.get("ingredients")
        ),

        how_to_use=(
            item.get("howToUse")
            or item.get("usage_instruction")
        ),

        warnings=(
            item.get("warnings")
            or item.get("disclaimer")
        ),

        extra_data={
            "uses": item.get("uses"),
            "rating": item.get("rating"),
            "highlights": item.get("highlights"),
            "key_features": item.get("keyFeatures"),
            "composition": item.get("composition"),
            "manufacturer": item.get("manufacturer"),
            "pack_size": item.get("pack_size"),
            "country_of_origin": item.get("country_of_origin"),
        }
    )


# -------------------------------
# Seed products
# -------------------------------
async def seed_products():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        files = [
            ("data/heartcare.json", "HeartCare"),
            ("data/oralcare.json", "OralCare"),
            ("data/diabetes.json", "Diabetes"),
            ("data/skincare.json", "SkinCare"),
        ]

        for path, category in files:
            data = load_json(path)

            if isinstance(data, dict):
                items = (
                    data.get("medications")
                    or data.get("product", {}).get("tablets")
                    or data.get("product", {}).get("insulin")
                    or []
                )
            else:
                items = data

            for item in items:
                db.add(map_product(item, category))

        await db.commit()
        print("✅ Default products inserted successfully")


if __name__ == "__main__":
    asyncio.run(seed_products())
