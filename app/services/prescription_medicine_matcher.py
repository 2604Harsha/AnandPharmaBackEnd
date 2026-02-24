import re
from sqlalchemy import select
from models.product import Product


# ----------------------------------
# CLEAN TEXT
# ----------------------------------
def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ----------------------------------
# MAIN MATCH FUNCTION
# ----------------------------------
async def match_products(db, extracted_text: str):
    """
    Returns:
        available_medicines
        unavailable_medicines
    """

    clean_text = normalize(extracted_text)

    # 🔹 Load products from DB
    result = await db.execute(select(Product))
    products = result.scalars().all()

    available = []
    unavailable = []
    matched_product_ids = set()

    # ----------------------------------
    # STEP 1 — Match available medicines
    # ----------------------------------
    for product in products:
        product_name_norm = normalize(product.name)

        if product_name_norm and product_name_norm in clean_text:
            matched_product_ids.add(product.id)

            available.append({
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "price": product.price,
                "image": product.image,
                "description": product.description
            })

    # ----------------------------------
    # STEP 2 — Extract medicine patterns
    # ----------------------------------
    # Handles:
    # paracetamol 500mg
    # paracetamol 500 mg
    # paracetamol-500mg
    # PARACETAMOL 500MG

    medicine_patterns = re.findall(
        r"[a-zA-Z]+\s*\d+\s*mg",
        clean_text
    )

    # normalize extracted medicines
    medicine_patterns = list(set(normalize(m) for m in medicine_patterns))

    # ----------------------------------
    # STEP 3 — Find unavailable medicines
    # ----------------------------------
    for med in medicine_patterns:
        found = False

        for product in products:
            product_name_norm = normalize(product.name)

            if product_name_norm and product_name_norm in med:
                found = True
                break

        if not found:
            unavailable.append(med)

    return available, list(set(unavailable))
