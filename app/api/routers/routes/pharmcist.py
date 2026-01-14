from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
 
from core.rbac import require_role
from core.database import get_db
from models.prescription import Prescription
from models.prescription_item import PrescriptionItem
from services.prescription_medicine_matcher import match_products
 
router = APIRouter(prefix="/pharmacist", tags=["Pharmacist"])
 
 
# ======================================================
# PHARMACIST VIEW PRESCRIPTION
# ======================================================
@router.get("/review/{prescription_id}")
async def review_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("pharmacist","ADMIN"))
):
    prescription = await db.get(Prescription, prescription_id)
 
    if not prescription:
        raise HTTPException(404, "Prescription not found")
 
    result = await db.execute(
        select(PrescriptionItem).where(
            PrescriptionItem.prescription_id == prescription_id
        )
    )
    items = result.scalars().all()
 
    return {
        "prescription_id": prescription.id,
        "status": prescription.status,
        # ✅ FIXED: file_path instead of image_path
        "prescription_image_url": f"/{prescription.file_path}",
        "detected_medicines": [
            {
                "medicine_name": item.medicine_name,
                "product_id": item.product_id
            }
            for item in items
        ]
    }
 
 
# ======================================================
# APPROVE PRESCRIPTION
# ======================================================
@router.post("/approve/{prescription_id}")
async def approve_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("pharmacist","ADMIN"))
):
    prescription = await db.get(Prescription, prescription_id)

    if not prescription:
        raise HTTPException(404, "Prescription not found")

    if prescription.status == "approved":
        return {"message": "Already approved"}

    # 🔹 Clear old items
    await db.execute(
        delete(PrescriptionItem).where(
            PrescriptionItem.prescription_id == prescription_id
        )
    )

    # 🔹 Match medicines AFTER approval
    available, unavailable = await match_products(
        db, prescription.extracted_text
    )

    # 🔹 Save available items
    for med in available:
        db.add(
            PrescriptionItem(
                prescription_id=prescription.id,
                product_id=med["id"],
                medicine_name=med["name"]
            )
        )

    prescription.status = "approved"
    await db.commit()

    return {
        "status": "approved",
        "prescription_id": prescription.id,
        "prescription_image": f"/{prescription.file_path}",
        "matched_products": available,
        "unavailable_medicines": unavailable
    }
 
 
# ======================================================
# REJECT PRESCRIPTION
# ======================================================
@router.post("/reject/{prescription_id}")
async def reject_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("pharmacist","ADMIN"))
):
    prescription = await db.get(Prescription, prescription_id)
 
    if not prescription:
        raise HTTPException(404, "Prescription not found")
 
    prescription.status = "rejected"
    await db.commit()
 
    return {
        "message": "Prescription rejected. Ask user to upload correct doctor prescription."
    }
 
 
 