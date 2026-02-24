from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.rbac import require_role
from core.database import get_db
from schemas.cart import AddToCartRequest
from services.cart_service import (
    add_to_cart,
    delete_cart_item,
    get_cart_items,
    update_cart_item
)

router = APIRouter(prefix="/cart", tags=["Cart"])


# 🛒 ADD TO CART
@router.post("/add")
async def add_product_to_cart(
    data: AddToCartRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    await add_to_cart(
        db,
        user_id=current_user.id,
        product_id=data.product_id,
        quantity=data.quantity
    )

    return {"message": "Product added to cart"}


# ✏️ UPDATE CART ITEM
@router.put("/update/{product_id}")
async def update_cart(
    product_id: int,
    quantity: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    updated = await update_cart_item(
        db,
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    return {"message": "Cart item updated successfully"}


# ❌ DELETE CART ITEM
@router.delete("/delete/{product_id}")
async def delete_cart(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    deleted = await delete_cart_item(
        db,
        user_id=current_user.id,
        product_id=product_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    return {"message": "Cart item removed successfully"}


# 👀 VIEW CART
@router.get("/view")
async def view_cart(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    items = await get_cart_items(db, current_user.id)

    return [
        {
            "product_id": item.product.id,
            "name": item.product.name,
            "category": item.product.category,
            "brand": item.product.brand,
            "price": item.product.price,
            "image": item.product.image,
            "quantity": item.quantity,

            # 🔥 CORRECT RX FLAG (IMPORTANT)
            "requires_prescription": item.product.is_rx
        }
        for item in items
    ]
