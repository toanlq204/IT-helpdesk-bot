from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TicketBase(BaseModel):
    title: str
    description: str
    priority: str = "medium"


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None


class TicketNoteCreate(BaseModel):
    body: str
    is_internal: bool = False


class TicketNoteResponse(BaseModel):
    id: int
    ticket_id: int
    author_id: int
    body: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketResponse(TicketBase):
    id: int
    created_by: int
    assigned_to: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    notes: List[TicketNoteResponse] = []

    class Config:
        from_attributes = True
