from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin, technician, user
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    created_tickets = relationship("Ticket", foreign_keys="[Ticket.created_by]", back_populates="creator")
    assigned_tickets = relationship("Ticket", foreign_keys="[Ticket.assigned_to]", back_populates="assignee")
    ticket_notes = relationship("TicketNote", back_populates="author")
    uploaded_documents = relationship("Document", back_populates="uploader")
    conversations = relationship("Conversation", back_populates="user")
