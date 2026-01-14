from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, JSON
)
from sqlalchemy.sql import func
from core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    # -----------------
    # Basic Info
    # -----------------
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    sub_category = Column(String(100))
    brand = Column(String(100))

    # -----------------
    # Pricing
    # -----------------
    price = Column(Float)
    original_price = Column(Float)
    discount = Column(Float)

    # -----------------
    # Stock (✅ OUTSIDE JSON)
    # -----------------
    stock = Column(Integer, default=0)

    # -----------------
    # Media
    # -----------------
    image = Column(String(255))

    # -----------------
    # Description
    # -----------------
    description = Column(Text)
    ingredients = Column(Text)
    how_to_use = Column(Text)
    warnings = Column(Text)

    # -----------------
    # Extra Flexible Data (NO stock here ❌)
    # -----------------
    extra_data = Column(JSON)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
