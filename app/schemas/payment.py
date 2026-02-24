from pydantic import BaseModel


# ==============================
# CREATE RAZORPAY ORDER
# ==============================
class CreatePaymentOrder(BaseModel):
    order_id: int
    amount: float


# ==============================
# VERIFY PAYMENT
# ==============================
class VerifyPayment(BaseModel):
    razorpay_order_id: str
    razorpay_key_id: str
    razorpay_signature: str
