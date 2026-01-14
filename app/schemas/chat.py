from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    reply: str
    items: Optional[List[Dict[str, Any]]] = None
    options: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None
