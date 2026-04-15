from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    query: str
    location: Optional[str] = "北京"

class ChatResponse(BaseModel):
    answer: str
    status: str = "success"
