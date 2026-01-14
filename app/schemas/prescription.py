from pydantic import BaseModel
from typing import List
 
 
class PrescriptionRequest(BaseModel):
    medicines: List[str]
 
 
class PrescriptionResponse(BaseModel):
    id: int
    name: str
    brand: str
    price: float
    image: str
    stock: int
 