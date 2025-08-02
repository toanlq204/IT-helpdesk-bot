from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    file_ids: List[str] = []

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    function_calls: List[str] = [] 