from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProductCreate(BaseModel):
    id: int
    name: str
    category: str
    sub_category: Optional[str] = None
    brand: Optional[str] = None

    price: Optional[float] = None
    original_price: Optional[float] = None
    discount: Optional[float] = None

    image: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[str] = None
    how_to_use: Optional[str] = None
    warnings: Optional[str] = None

    extra_data: Optional[Dict[str, Any]] = None


class ProductResponse(ProductCreate):
    id: int
    created_at: datetime

class ProductDetailResponse(BaseModel):
    id: int
    name: str
    category: str
    sub_category: Optional[str]
    brand: Optional[str]

    price: Optional[float]
    original_price: Optional[float]
    discount: Optional[float]
    stock: Optional[int]
    image: Optional[str]
    description: Optional[str]
    ingredients: Optional[str]
    how_to_use: Optional[str]
    warnings: Optional[str]

    extra_data: Optional[Dict[str, Any]]
    created_at: datetime



class ProductUserResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    price: Optional[float]
    original_price: Optional[float]
    discount: Optional[float]
    stock: Optional[int]
    image: Optional[str]
    description: Optional[str]

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    stock: Optional[int]
    discount: Optional[float] = None
    image: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[str] = None
    how_to_use: Optional[str] = None
    warnings: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class ProductListResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    data: List[ProductResponse]

    class Config:
        from_attributes = True

