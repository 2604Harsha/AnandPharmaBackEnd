import asyncio
from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.user import User
from core.security import hash_password


ADMIN_EMAIL = "admin@pharma.com"
ADMIN_PASSWORD = "Admin@123"


async def create_admin():
    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(User).where(User.email == ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()

        if admin:
            print("\n⚠️  Admin already exists")
            print(f"📧 Email    : {ADMIN_EMAIL}")
            print("🔑 Password : (already set)\n")
            return

        admin = User(
            full_name="Admin",
            email=ADMIN_EMAIL,
            password=hash_password(ADMIN_PASSWORD),
            role="ADMIN",
            is_active=True,
            is_verified=True
        )

        db.add(admin)
        await db.commit()

        # ✅ SHOW DETAILS ONLY HERE
        print("\n✅ Admin created successfully")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📧 Email    : {ADMIN_EMAIL}")
        print(f"🔑 Password : {ADMIN_PASSWORD}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


if __name__ == "__main__":
    asyncio.run(create_admin())
