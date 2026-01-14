import asyncio

from core.database import engine, Base

import models  


async def reset_database():
    async with engine.begin() as conn:
        print("⚠️ Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)

        print("✅ Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)

        print("\n📦 Tables registered:")
        for table in Base.metadata.tables.keys():
            print(" -", table)

    print("\n🎉 Database reset completed successfully")


if __name__ == "__main__":
    asyncio.run(reset_database())
