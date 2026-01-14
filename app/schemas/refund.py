from typing import Optional
from pydantic import BaseModel
from enum import Enum
 
 
class RefundReasonEnum(str, Enum):
    cancelled = "cancelled"
    out_of_stock = "out_of_stock"
    prescription_rejected = "prescription_rejected"
    damaged = "damaged"
    wrong_item = "wrong_item"
    payment_failure = "payment_failure"
 
 
class RefundCreate(BaseModel):
    order_id: int
    payment_id: str
    amount: float
    reason: RefundReasonEnum
 
 
class RefundResponse(BaseModel):
    refund_id: int
    status: str
    amount: float
 