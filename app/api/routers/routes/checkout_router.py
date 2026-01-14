from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
 
from core.database import get_db
from core.rbac import require_role
from schemas.checkout import ShippingAddressCreate
 
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.order_address import OrderAddress
from models.cart import Cart
from models.cart_item import CartItem
from models.product import Product
 
from services.geocoding_service import geocode_address
 
router = APIRouter(prefix="/checkout", tags=["Checkout"])
 
 
# ======================================================
# MOVE CART → ORDER ITEMS
# ======================================================
async def move_cart_to_order(db: AsyncSession, order_id: int, user_id: int):
    result = await db.execute(
        select(CartItem, Product)
        .join(Cart, CartItem.cart_id == Cart.id)
        .join(Product, CartItem.product_id == Product.id)
        .where(Cart.user_id == user_id)
    )
 
    rows = result.all()
    if not rows:
        raise HTTPException(400, "Cart is empty")
 
    subtotal = 0
 
    for cart_item, product in rows:
        subtotal += product.price * cart_item.quantity
 
        db.add(
            OrderItem(
                order_id=order_id,
                product_id=product.id,
                product_name=product.name,
                quantity=cart_item.quantity,
                price=product.price,
            )
        )
        await db.delete(cart_item)
 
    tax = round(subtotal * 0.18, 2)
    total = subtotal + tax
 
    order = await db.get(Order, order_id)
    order.subtotal = subtotal
    order.tax = tax
    order.total = total
 
 
# ======================================================
# 🧾 CHECKOUT SUMMARY (CART BASED) ✅
# ======================================================
@router.get("/summary")
async def checkout_summary(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("user")),
):
    result = await db.execute(
        select(CartItem, Product)
        .join(Cart, CartItem.cart_id == Cart.id)
        .join(Product, CartItem.product_id == Product.id)
        .where(Cart.user_id == user.id)
    )
 
    rows = result.all()
    if not rows:
        raise HTTPException(400, "Cart is empty")
 
    items = []
    subtotal = 0
 
    for cart_item, product in rows:
        line_total = product.price * cart_item.quantity
        subtotal += line_total
 
        items.append({
            "name": product.name,
            "price": product.price,
            "qty": cart_item.quantity,
            "line_total": line_total,
        })
 
    tax = round(subtotal * 0.18, 2)
 
    return {
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": 0,
        "total": subtotal + tax,
    }
 
 
# ======================================================
# SAVE ADDRESS + CREATE ORDER ✅ FIXED
# ======================================================
@router.post("/address")
async def save_shipping_address(
    payload: ShippingAddressCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("user")),
):
    order = Order(user_id=user.id, status=OrderStatus.PENDING)
    db.add(order)
    await db.flush()
 
    # 🔹 Convert address → lat/lng
    full_address = f"{payload.address}, {payload.city}, {payload.pincode}"
    latitude, longitude = geocode_address(full_address)
 
    db.add(
        OrderAddress(
            order_id=order.id,
            address=payload.address,
            city=payload.city,
            pincode=payload.pincode,
            latitude=latitude,
            longitude=longitude,
        )
    )
 
    await move_cart_to_order(db, order.id, user.id)
    await db.commit()
 
    return {
        "order_id": order.id,
        "status": order.status,
        "latitude": latitude,
        "longitude": longitude,
    }
 
 
# ======================================================
# REVIEW ORDER
# ======================================================
@router.get("/review/{order_id}")
async def review_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("user")),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
 
    items = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
 
    return {
        "order_id": order.id,
        "total": order.total,
        "status": order.status,
        "items": [
            {"name": i.product_name, "qty": i.quantity, "price": i.price}
            for i in items.scalars()
        ],
    }
 
 
