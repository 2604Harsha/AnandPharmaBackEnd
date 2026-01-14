import pandas as pd
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.product import Product
from schemas.product import ProductCreate, ProductUpdate, ProductUserResponse


def parse_list(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return [i.strip() for i in value.split("|")]
    return None


def clean_value(value):
    if pd.isna(value):
        return None
    return value

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except:
        return default

def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except:
        return default
    
    
# -------------------------------
# Create Product
# -------------------------------
async def create_product(db: AsyncSession, data: ProductCreate):
    product = Product(**data.dict())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


# -------------------------------
# Get All Products
# -------------------------------
async def get_all_products(db: AsyncSession):
    result = await db.execute(select(Product))
    return result.scalars().all()


# -------------------------------
# Get Products by Category
# -------------------------------
async def get_products_by_category_service(category: str, db: AsyncSession):
    result = await db.execute(
        select(Product).where(Product.category.ilike(category))
    )
    products = result.scalars().all()

    if not products:
        raise HTTPException(404, "No products found")

    return [
        ProductUserResponse(
            id=p.id,
            name=p.name,
            brand=p.brand,
            price=p.price,
            original_price=p.original_price,
            discount=p.discount,
            stock=p.stock,
            image=p.image,
            description=p.description,
        )
        for p in products
    ]


# -------------------------------
# Get Product Details
# -------------------------------
async def get_product_details_service(product_id: int, db: AsyncSession):
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(404, "Product not found")

    return product


# -------------------------------
# Import Products from Excel
# -------------------------------
async def import_products_from_excel(file_path: str, db: AsyncSession):
    df = pd.read_excel(file_path)

    created = 0
    updated = 0

    for _, row in df.iterrows():

        name = clean_value(row.get("name"))
        brand = clean_value(row.get("brand"))
        category = clean_value(row.get("category"))

        incoming_stock = (
            int(row.get("stock"))
            if not pd.isna(row.get("stock"))
            else 1
        )

        # 🔍 Case-insensitive product match
        result = await db.execute(
            select(Product).where(
                func.lower(Product.name) == name.lower(),
                func.lower(Product.brand) == brand.lower(),
                func.lower(Product.category) == category.lower(),
            )
        )

        product = result.scalars().first()

        if product:
            # ✅ INCREASE STOCK
            product.stock = (product.stock or 0) + incoming_stock
            updated += 1
            continue

        # ➕ CREATE NEW PRODUCT
        new_product = Product(
            name=name,
            category=category,
            sub_category=clean_value(row.get("sub_category")),
            brand=brand,
            price=safe_float(row.get("price")),
            original_price=safe_float(row.get("original_price")),
            discount=safe_float(row.get("discount")),
            stock=incoming_stock,
            image=clean_value(row.get("image")),
            description=clean_value(row.get("description")),
            ingredients=clean_value(row.get("ingredients")),
            how_to_use=clean_value(row.get("how_to_use")),
            warnings=clean_value(row.get("warnings")),
            extra_data={
                "uses": clean_value(row.get("uses")),
                "rating": clean_value(row.get("rating")),
                "highlights": clean_value(row.get("highlights")),
                "key_features": parse_list(row.get("key_features")),
                "composition": clean_value(row.get("composition")),
                "manufacturer": clean_value(row.get("manufacturer")),
                "pack_size": clean_value(row.get("pack_size")),
                "country_of_origin": clean_value(row.get("country_of_origin")),
            }
        )

        db.add(new_product)
        created += 1

    await db.commit()

    return {
        "message": "Import completed successfully",
        "created_products": created,
        "updated_stock_products": updated,
    }



# -------------------------------
# Update Product
# -------------------------------
async def update_product_service(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession
):
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(404, "Product not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


# -------------------------------
# Delete Product
# -------------------------------
async def delete_product_service(product_id: int, db: AsyncSession):
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(404, "Product not found")

    await db.delete(product)
    await db.commit()

    return {"message": "Product deleted successfully"}


# -------------------------------
# Search Products by Name (Chatbot / Search)
# -------------------------------
async def search_products_by_name(db: AsyncSession, keyword: str):
    """
    Used by chatbot & search.
    Matches medicine name partially (case-insensitive).
    Example: 'atorvastatin' → 10mg, 20mg, 40mg variants
    """
 
    result = await db.execute(
        select(Product).where(
            func.lower(Product.name).ilike(f"%{keyword.lower()}%")
        )
    )
 
    return result.scalars().all()
