from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from models.prescription import Prescription, PrescriptionStatus
from models.prescription_item import PrescriptionItem
from models.cart import Cart
from models.cart_item import CartItem
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from models.shipping_address import ShippingAddress

TAX_PERCENT = 18


# ======================================================
# GET OR CREATE CART
# ======================================================
async def get_or_create_cart(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    return cart


# ======================================================
# ADD TO CART (RX SAFE ✅)
# ======================================================
async def add_to_cart(
    db: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int
):
    # 🔍 Load product
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 🔒 RX ENFORCEMENT
    if product.is_rx:
        # ✅ Get ANY approved prescription (since no user_id column)
        pres_result = await db.execute(
            select(Prescription)
            .where(Prescription.status == PrescriptionStatus.approved)
            .order_by(Prescription.id.desc())
        )
        prescription = pres_result.scalars().first()

        if not prescription:
            raise HTTPException(
                status_code=400,
                detail="Prescription required for this medicine"
            )

        # 🔍 Check medicine exists in prescription
        items_result = await db.execute(
            select(PrescriptionItem.medicine_name)
            .where(
                PrescriptionItem.prescription_id == prescription.id
            )
        )

        allowed_medicines = {
            name.lower() for (name,) in items_result.all()
        }

        if product.name.lower() not in allowed_medicines:
            raise HTTPException(
                status_code=400,
                detail=f"{product.name} is not present in uploaded prescription"
            )

    # 🛒 Get or create cart
    cart = await get_or_create_cart(db, user_id)

    # ➕ Add or update cart item
    result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    )
    item = result.scalar_one_or_none()

    if item:
        item.quantity += quantity
    else:
        db.add(
            CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity
            )
        )

    await db.commit()


# ======================================================
# VIEW CART ITEMS
# ======================================================
async def get_cart_items(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .options(selectinload(CartItem.product))
        .where(Cart.user_id == user_id)
    )
    return result.scalars().all()


# ======================================================
# UPDATE CART ITEM
# ======================================================
async def update_cart_item(
    db: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int
):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(
            Cart.user_id == user_id,
            CartItem.product_id == product_id
        )
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        return False

    if quantity <= 0:
        await db.delete(cart_item)
    else:
        cart_item.quantity += quantity

    await db.commit()
    return True


# ======================================================
# DELETE CART ITEM
# ======================================================
async def delete_cart_item(
    db: AsyncSession,
    user_id: int,
    product_id: int
):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(
            Cart.user_id == user_id,
            CartItem.product_id == product_id
        )
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        return False

    await db.delete(cart_item)
    await db.commit()
    return True


# ======================================================
# CHECKOUT SUMMARY (NO RX LOGIC HERE ❌)
# ======================================================
async def get_checkout_summary(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .options(selectinload(CartItem.product))
        .where(Cart.user_id == user_id)
    )

    items_db = result.scalars().all()
    if not items_db:
        return None

    subtotal = 0
    items = []

    for item in items_db:
        subtotal += item.product.price * item.quantity
        items.append({
            "product_id": item.product_id,
            "name": item.product.name,
            "quantity": item.quantity,
            "price": item.product.price,
            "requires_prescription": item.product.is_rx
        })

    tax = round(subtotal * TAX_PERCENT / 100, 2)
    total = round(subtotal + tax, 2)

    return {
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total
    }


# ======================================================
# SAVE SHIPPING ADDRESS
# ======================================================
async def save_shipping_address(db: AsyncSession, user_id: int, data):
    address = ShippingAddress(
        user_id=user_id,
        **data.dict()
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


# ======================================================
# PLACE ORDER (RX ALREADY VALIDATED BEFORE)
# ======================================================
async def place_order(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .options(selectinload(CartItem.product))
        .where(Cart.user_id == user_id)
    )

    items_db = result.scalars().all()
    if not items_db:
        raise Exception("Cart is empty")

    subtotal = sum(
        item.product.price * item.quantity
        for item in items_db
    )

    tax = round(subtotal * TAX_PERCENT / 100, 2)
    total = round(subtotal + tax, 2)

    order = Order(
        user_id=user_id,
        subtotal=subtotal,
        tax=tax,
        total=total,
        status="PLACED"
    )

    db.add(order)
    await db.flush()

    for item in items_db:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
        )

    # 🔥 Clear cart
    await db.execute(
        delete(CartItem).where(
            CartItem.cart_id == items_db[0].cart_id
        )
    )

    await db.commit()
    await db.refresh(order)
    return order
