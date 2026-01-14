import random

OTP_TTL = 300  # 5 minutes

class DeliveryOTPService:

    @staticmethod
    async def generate(redis, order_id):
        otp = random.randint(1000, 9999)
        await redis.setex(f"delivery:otp:{order_id}", OTP_TTL, otp)
        return otp

    @staticmethod
    async def verify(redis, order_id, otp):
        key = f"delivery:otp:{order_id}"
        saved = await redis.get(key)

        if not saved or saved != str(otp):
            return False

        await redis.delete(key)
        return True
