from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    filename: str
    content_type: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    filepath: str
    size_bytes: int
    uploaded_by: int
    uploaded_at: datetime
    status: str

    class Config:
        from_attributes = True


class DocumentTextResponse(BaseModel):
    id: int
    document_id: int
    text: str
    char_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentWithText(DocumentResponse):
    document_text: Optional[DocumentTextResponse] = None
