import os
import shutil
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.rbac import require_role
from core.database import get_db
from models.product import Product
from schemas.product import ProductCreate, ProductDetailResponse, ProductListResponse, ProductResponse, ProductUpdate, ProductUserResponse
from services.product_service import delete_product_service, get_all_products, get_product_details_service, get_products_by_category_service, import_products_from_excel, update_product_service

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/import-excel")
async def import_products(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role("pharmacist","ADMIN"))
):
    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    response = await import_products_from_excel(
        file_path=file_path,
        db=db
    )

    os.remove(file_path)

    return response

@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_products(db, page, limit)

@router.get(
    "/category/{category}",
    response_model=list[ProductUserResponse]
)
async def get_products_by_category(
    category: str,
    db: AsyncSession = Depends(get_db)
):
    return await get_products_by_category_service(
        category=category,
        db=db
    )

@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse
)
async def get_product_details(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role("user"))
):
    return await get_product_details_service(
        product_id=product_id,
        db=db
    )



@router.put(
    "/{product_id}",
    response_model=ProductDetailResponse
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role("pharmacist","ADMIN"))
):
    return await update_product_service(
        product_id=product_id,
        data=data,
        db=db
    )

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role("pharmacist","ADMIN"))
):
    return await delete_product_service(
        product_id=product_id,
        db=db
    )
