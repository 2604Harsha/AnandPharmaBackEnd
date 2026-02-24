from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.redis import get_redis
from core.rbac import require_role

from schemas.checkout import ShippingAddressCreate

from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.order_address import OrderAddress
from models.cart import Cart
from models.cart_item import CartItem
from models.product import Product
from models.prescription import Prescription, PrescriptionStatus
from models.prescription_item import PrescriptionItem

from services.geocoding_service import geocode_address
from services.pricing_service import calculate_pricing
from services.surge_service import get_active_surge

router = APIRouter(prefix="/checkout", tags=["Checkout"])


# ======================================================
# 🧾 CHECKOUT SUMMARY (NO DELIVERY / NO SURGE)
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
    rx_required = False

    for cart_item, product in rows:
        line_total = product.price * cart_item.quantity
        subtotal += line_total

        if product.is_rx:
            rx_required = True

        items.append({
            "name": product.name,
            "price": product.price,
            "qty": cart_item.quantity,
            "line_total": line_total,
            "requires_prescription": product.is_rx,
        })

    pricing = calculate_pricing(subtotal)

    return {
        "items": items,
        "subtotal": subtotal,
        "cgst": pricing["cgst"],
        "sgst": pricing["sgst"],
        "handling_fee": pricing["handling_fee"],
        "delivery_fee": 0,
        "surge_fee": 0,
        "estimated_total": (
            subtotal
            + pricing["cgst"]
            + pricing["sgst"]
            + pricing["handling_fee"]
        ),
        "rx_required": rx_required,
        "note": (
            "Prescription approval required before checkout"
            if rx_required
            else "Delivery & surge charges will be added after address"
        )
    }


# ======================================================
# MOVE CART → ORDER ITEMS (LOCK FINAL PRICING)
# ======================================================
async def move_cart_to_order(
    db: AsyncSession,
    order_id: int,
    user_id: int,
    redis,
):
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

    surge_fee = await get_active_surge(redis)
    pricing = calculate_pricing(subtotal, surge_fee)

    order = await db.get(Order, order_id)
    order.subtotal = subtotal
    order.cgst = pricing["cgst"]
    order.sgst = pricing["sgst"]
    order.handling_fee = pricing["handling_fee"]
    order.delivery_fee = pricing["delivery_fee"]
    order.surge_fee = pricing["surge_fee"]
    order.total = pricing["total"]


# ======================================================
# SAVE ADDRESS → APPLY DELIVERY & SURGE
# ======================================================
@router.post("/address")

async def save_shipping_address(

    payload: ShippingAddressCreate,

    db: AsyncSession = Depends(get_db),

    redis=Depends(get_redis),

    user=Depends(require_role("user")),

):

    # 🔒 RX FINAL VALIDATION

    result = await db.execute(

        select(CartItem, Product)

        .join(Cart, CartItem.cart_id == Cart.id)

        .join(Product, CartItem.product_id == Product.id)

        .where(Cart.user_id == user.id)

    )
 
    rows = result.all()

    rx_products = [product for _, product in rows if product.is_rx]
 
    if rx_products:

        # ✅ GET LATEST APPROVED PRESCRIPTION

        pres_q = await db.execute(

            select(Prescription)

            .where(Prescription.status == PrescriptionStatus.approved)

            .order_by(Prescription.id.desc())

        )

        prescription = pres_q.scalars().first()
 
        if not prescription:

            raise HTTPException(

                400,

                "Prescription medicines present. Upload & get prescription approved."

            )
 
        # 🔍 ALLOWED MEDICINES FROM PRESCRIPTION

        items_q = await db.execute(

            select(PrescriptionItem.medicine_name)

            .where(PrescriptionItem.prescription_id == prescription.id)

        )

        allowed = {m[0].lower() for m in items_q.all()}
 
        for product in rx_products:

            if product.name.lower() not in allowed:

                raise HTTPException(

                    400,

                    f"{product.name} not covered in uploaded prescription"

                )
 
    # ✅ CREATE ORDER

    order = Order(user_id=user.id, status=OrderStatus.PENDING)

    db.add(order)

    await db.flush()
 
    full_address = f"{payload.address}, {payload.city}, {payload.pincode}"

    lat, lng = geocode_address(full_address)
 
    db.add(

        OrderAddress(

            order_id=order.id,

            address=payload.address,

            city=payload.city,

            pincode=payload.pincode,

            latitude=lat,

            longitude=lng,

        )

    )
 
    await move_cart_to_order(db, order.id, user.id, redis)

    await db.commit()
 
    return {

        "order_id": order.id,

        "status": order.status,

        "latitude": lat,

        "longitude": lng,

        "message": "Delivery & surge charges applied. Order ready for review 🧾"

    }

 

# ======================================================
# 🧾 REVIEW ORDER (FINAL BILL)
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
        "subtotal": order.subtotal,
        "cgst": order.cgst,
        "sgst": order.sgst,
        "handling_fee": order.handling_fee,
        "delivery_fee": order.delivery_fee,
        "surge_fee": order.surge_fee,
        "total": order.total,
        "items": [
            {
                "name": i.product_name,
                "qty": i.quantity,
                "price": i.price
            }
            for i in items.scalars()
        ]
    }
