from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, JSON, Boolean
)
from sqlalchemy.sql import func
from core.database import Base
from core.rx_rules import is_prescription_required


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
    # RX / OTC Classification
    # -----------------
    medicine_class = Column(String(20), default="OTC")  
    
    # OTC | RX | DEVICE | WELLNESS
    requires_prescription = Column(Boolean, default=False)


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


    @property
    def is_rx(self) -> bool:
        return is_prescription_required(
            self.category,
            self.name,
            self.extra_data
        )
