from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.product import Product
from docx import Document
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import re
 
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
 
 
# ----------------------------------
# TEXT EXTRACTION
# ----------------------------------
async def extract_text(file: UploadFile) -> str:
    content = await file.read()
    name = file.filename.lower()
 
    if name.endswith(".pdf"):
        doc = fitz.open(stream=content, filetype="pdf")
        return " ".join(page.get_text() for page in doc)
 
    elif name.endswith(".docx"):
        doc = Document(io.BytesIO(content))
        return " ".join(p.text for p in doc.paragraphs)
 
    elif name.endswith((".jpg", ".jpeg", ".png")):
        img = Image.open(io.BytesIO(content))
        return pytesseract.image_to_string(img)
 
    elif name.endswith(".txt"):
        return content.decode("utf-8")
 
    else:
        raise HTTPException(400, "Unsupported file format")
 
 
# ----------------------------------
# CLEAN TEXT
# ----------------------------------
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
 
 
# ----------------------------------
# MAIN LOGIC
# ----------------------------------
async def process_prescription(file: UploadFile, db: AsyncSession):
    raw_text = await extract_text(file)
    clean_text = normalize(raw_text)
 
    # Load all medicines from DB
    result = await db.execute(select(Product))
    products = result.scalars().all()
 
    available = []
    unavailable = []
 
    matched_names = set()
 
    for product in products:
        product_name = normalize(product.name)
 
        # Match ignoring dosage formatting
        if product_name in clean_text:
            matched_names.add(product_name)
            available.append({
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "price": product.price,
                "image": product.image,
                "description": product.description
            })
 
    # Extract possible medicine-like phrases
    words = re.findall(r"[a-z]+\s?\d+mg", clean_text)
 
    for w in words:
        if w not in matched_names:
            unavailable.append(w)
 
    return {
        "available_medicines": available,
        "unavailable_medicines": list(set(unavailable))
    }