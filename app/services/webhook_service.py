import hmac
import hashlib
from core.config import RAZORPAY_WEBHOOK_SECRET

class WebhookService:

    def verify_razorpay(self, body: bytes, signature: str):
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
