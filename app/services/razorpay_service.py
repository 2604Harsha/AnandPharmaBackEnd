
import razorpay
import uuid
import asyncio
from core.config import settings


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
        # ✅ MOCK RESPONSE
        if settings.PAYMENT_MODE != "RAZORPAY":
            return {
                "id": f"order_mock_{uuid.uuid4().hex}",
                "amount": int(amount * 100),
                "currency": currency,
                "status": "created",
            }

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.client.order.create,
            {
                "amount": int(amount * 100),
                "currency": currency,
                "payment_capture": 1,
            },
        )

    async def verify_payment(self, order_id, payment_id, signature):
        # ✅ MOCK VERIFY ALWAYS SUCCESS
        if settings.PAYMENT_MODE != "RAZORPAY":
            return True

        data = {
            "razorpay_order_id": order_id,
            "razorpay_test_id": payment_id,
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

