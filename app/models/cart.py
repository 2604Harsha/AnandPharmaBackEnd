from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, unique=True)

    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )

