from pydantic import BaseModel
from typing import Optional

class AgentLocationUpdate(BaseModel):
    address: str
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = None
