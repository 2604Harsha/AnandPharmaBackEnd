from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.order import Order

async def get_order_by_number(db, order_number: str):
    result = await db.execute(
        select(Order)
        .where(Order.order_number == order_number)
        .options(selectinload(Order.items))
    )
    return result.scalars().first()
