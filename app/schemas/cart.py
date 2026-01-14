from pydantic import BaseModel


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1


class CartProductResponse(BaseModel):
    product_id: int
    name: str
    category: str
    brand: str
    price: float
    image: str
    quantity: int

    class Config:
        from_attributes = True

