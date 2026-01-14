from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from models.cart import Cart
from models.cart_item import CartItem
from models.order import Order
from models.order_item import OrderItem
from models.shipping_address import ShippingAddress

TAX_PERCENT = 18

async def get_checkout_summary(db, user_id: int):
    result = await db.execute(
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.product)
        )
        .where(Cart.user_id == user_id)
    )

    cart = result.scalar_one_or_none()

    if not cart or not cart.items:
        return None

    subtotal = 0
    items = []

    for item in cart.items:
        price = item.product.price
        subtotal += price * item.quantity

        items.append({
            "product_id": item.product_id,
            "name": item.product.name,
            "quantity": item.quantity,
            "price": price
        })

    tax = round(subtotal * TAX_PERCENT / 100, 2)
    total = round(subtotal + tax, 2)

    return {
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total
    }

async def save_shipping_address(db, user_id: int, data):
    address = ShippingAddress(
        user_id=user_id,
        **data.dict()
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


async def place_order(db, user_id: int, address_id: int):

    # 🔹 Validate address
    result = await db.execute(
        select(ShippingAddress).where(
            ShippingAddress.id == address_id,
            ShippingAddress.user_id == user_id
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(400, "Invalid address")

    # 🔹 Get cart
    result = await db.execute(
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.product)
        )
        .where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()

    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty")

    # 🔹 Calculate totals
    subtotal = sum(
        item.product.price * item.quantity
        for item in cart.items
    )

    tax = round(subtotal * TAX_PERCENT / 100, 2)
    total = round(subtotal + tax, 2)

    # 🔹 Create order
    order = Order(
        user_id=user_id,
        subtotal=subtotal,
        tax=tax,
        total=total,
        status="PLACED"
    )

    db.add(order)
    await db.flush()  # ✅ order.id available here

    # 🔹 Generate ORD001
    order.order_number = f"ORD{order.id:03d}"

    # 🔹 Attach address
    address.order_id = order.id

    # 🔹 Create order items
    for item in cart.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
        )

    # 🔹 Clear cart
    await db.execute(
        delete(CartItem).where(CartItem.cart_id == cart.id)
    )

    await db.commit()
    await db.refresh(order)

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "total": order.total
    }
