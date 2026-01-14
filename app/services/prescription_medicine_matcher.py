 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.product import Product
import re
from typing import List, Dict, Tuple
 
 
# --------------------------------------------------
# NORMALIZATION
# --------------------------------------------------
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\d+\s?(mg|ml|mcg|g)", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
 
 
# --------------------------------------------------
# EXTRACT MEDICINE CANDIDATES FROM PRESCRIPTION
# --------------------------------------------------
def extract_medicine_candidates(text: str) -> List[str]:
    """
    Extract possible medicine names from OCR text.
    Uses common prescription patterns.
    """
    candidates = set()
    lines = text.lower().splitlines()
 
    MED_HINTS = ["tab", "tablet", "cap", "capsule", "inj", "syrup"]
 
    for line in lines:
        if any(hint in line for hint in MED_HINTS):
            words = re.findall(r"[a-z]{4,}", line)
            if words:
                candidates.add(words[0])  # first meaningful word
 
    return list(candidates)
 
 
# --------------------------------------------------
# MAIN MATCH FUNCTION
# --------------------------------------------------
async def match_products(
    db: AsyncSession,
    extracted_text: str
) -> Tuple[List[Dict], List[Dict]]:
 
    normalized_text = normalize(extracted_text)
 
    # 1️⃣ Load all products
    products = (await db.execute(select(Product))).scalars().all()
 
    available = []
    matched_names = set()
 
    # 2️⃣ Match DB medicines
    for product in products:
        pname = normalize(product.name)
 
        if pname and pname in normalized_text:
            base = pname.split()[0]
            matched_names.add(base)

            available.append({
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "price": product.price,
                "image": product.image,      
                "description": product.description  
            })
 
    # 3️⃣ Extract medicine names from prescription
    candidates = extract_medicine_candidates(extracted_text)
 
    # 4️⃣ Anything not matched → unavailable
    unavailable = []
    for cand in candidates:
        if cand not in matched_names:
            unavailable.append({
                "name": cand,
                "image": None,
                "description": "Not available in store"
            })
 
    return available, unavailable
 
 