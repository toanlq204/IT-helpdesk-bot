from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    status: str = "open"
    assignee: Optional[str] = None

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None

class Ticket(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    status: str
    assignee: Optional[str] = None
    created_at: str
    updated_at: str 