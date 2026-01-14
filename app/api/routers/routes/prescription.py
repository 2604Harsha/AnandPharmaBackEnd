from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import shutil, os
 
from core.rbac import require_role
from core.database import get_db
from services.ocr_service import extract_text
from services.prescription_validator import has_doctor_details
from services.prescription_medicine_matcher import match_products
from models.prescription import Prescription, PrescriptionStatus
from models.prescription_item import PrescriptionItem
 
router = APIRouter(prefix="/prescription", tags=["Prescription"])
 
UPLOAD_DIR = "uploads/prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)
 
 
# ======================================================
# UPLOAD PRESCRIPTION
# ======================================================
@router.post("/upload")
async def upload_prescription(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    # 1️⃣ Save file
    file_path = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2️⃣ OCR
    extracted_text = extract_text(file_path)

    # 3️⃣ Doctor validation
    has_details = has_doctor_details(extracted_text)

    status = (
        PrescriptionStatus.approved
        if has_details
        else PrescriptionStatus.pharmacist_review
    )

    # 4️⃣ Save prescription
    prescription = Prescription(
        file_path=file_path,
        extracted_text=extracted_text,
        status=status
    )

    db.add(prescription)
    await db.commit()
    await db.refresh(prescription)

    # 5️⃣ Match medicines (always calculate)
    available, unavailable = await match_products(db, extracted_text)

    # 🔒 Pharmacist review
    if status == PrescriptionStatus.pharmacist_review:
        return {
            "status": status,
            "prescription_id": prescription.id,
            "prescription_image": f"/{prescription.file_path}",
            "available_medicines": [],
            "unavailable_medicines": unavailable,
            "message": "Sent for pharmacist review (doctor details missing)"
        }

    # ✅ Auto approved
    return {
        "status": status,
        "prescription_id": prescription.id,
        "prescription_image": f"/{prescription.file_path}",
        "available_medicines": available,
        "unavailable_medicines": unavailable,
        "message": "Prescription auto-approved"
    }
 
 
# ======================================================
# GET PRESCRIPTION BY ID
# =====================================================
 
# ======================================================
@router.get("/{prescription_id}")
async def get_prescription_by_id(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    prescription = await db.get(Prescription, prescription_id)
 
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
 
    # Base response
    response = {
        "prescription_id": prescription.id,
        "status": prescription.status,
        "prescription_image": f"/{prescription.file_path}",
        "available_medicines": [],
        "unavailable_medicines": []
    }
 
    # 🔒 If NOT approved → return empty lists
    if prescription.status != PrescriptionStatus.approved:
        return response
 
    # ✅ If approved → calculate medicines NOW
    available, unavailable = await match_products(
        db,
        prescription.extracted_text
    )
 
    response["available_medicines"] = available
    response["unavailable_medicines"] = unavailable
 
    return response
 

