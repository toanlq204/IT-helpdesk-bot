from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class ChatStart(BaseModel):
    pass


class ChatMessage(BaseModel):
    session_id: str
    message: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    session_id: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    reply: str
    citations: List[Dict[str, str]] = []


class ChatStartResponse(BaseModel):
    session_id: str
