from pydantic import BaseModel, EmailStr
from typing import List


class ShippingAddressCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    state: str
    pincode: str
    landmark: str


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderSummaryResponse(BaseModel):
    order_id: int
    items: List[OrderItemResponse]
    subtotal: float
    tax: float
    total: float
