import razorpay
import uuid
import asyncio
from core.config import settings
from utils.payment_id import generate_payment_id   # ✅ import

class RazorpayService:
    def __init__(self):
        # ✅ MOCK MODE
        if settings.PAYMENT_MODE != "RAZORPAY":
            self.client = None
            return

        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise RuntimeError("Razorpay keys missing")

        self.client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID.strip(),
                settings.RAZORPAY_KEY_SECRET.strip(),
            )
        )

    async def create_order(self, amount: float, currency: str = "INR"):
        payment_id = generate_payment_id()   # ✅ your unique payment id

        # ✅ MOCK RESPONSE
        if settings.PAYMENT_MODE != "RAZORPAY":
            return {
                "id": f"order_mock_{uuid.uuid4().hex}",
                "amount": int(amount * 100),
                "currency": currency,
                "status": "created",
                "payment_id": payment_id,    # ✅ add here
            }

        loop = asyncio.get_running_loop()

        order = await loop.run_in_executor(
            None,
            self.client.order.create,
            {
                "amount": int(amount * 100),
                "currency": currency,
                "payment_capture": 1,
                "receipt": payment_id,   # ✅ store in Razorpay itself
            },
        )

        # ✅ return to frontend
        order["payment_id"] = payment_id
        return order

    async def verify_payment(self, order_id, payment_id, signature):
        # ✅ MOCK VERIFY ALWAYS SUCCESS
        if settings.PAYMENT_MODE != "RAZORPAY":
            return True

        data = {
            "razorpay_order_id": order_id,
            "razorpay_key_id": payment_id,   # ✅ FIXED KEY NAME
            "razorpay_signature": signature,
        }

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self.client.utility.verify_payment_signature,
            data,
        )

        return True

razorpay_service = RazorpayService()
