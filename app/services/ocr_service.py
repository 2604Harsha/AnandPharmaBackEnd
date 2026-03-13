
import pytesseract
from PIL import Image
import pdfplumber
from docx import Document

# ✅ Tell pytesseract where tesseract.exe is installed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text(file_path: str) -> str:

    # 🖼 IMAGE
    if file_path.lower().endswith((".jpg", ".jpeg", ".png")):
        return pytesseract.image_to_string(Image.open(file_path), lang="eng")

    # 📄 PDF
    if file_path.lower().endswith(".pdf"):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    # 📝 WORD
    if file_path.lower().endswith((".doc", ".docx")):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    return ""