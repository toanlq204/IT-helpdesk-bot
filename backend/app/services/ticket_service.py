from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models.ticket import Ticket, TicketNote
from ..models.user import User
from ..schemas.ticket import TicketCreate, TicketUpdate, TicketNoteCreate
from datetime import datetime


def create_ticket(db: Session, ticket: TicketCreate, user_id: int) -> Ticket:
    """Create a new ticket"""
    db_ticket = Ticket(
        created_by=user_id,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        status="open"
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_tickets_for_user(db: Session, user: User) -> List[Ticket]:
    """Get tickets based on user role"""
    if user.role == "admin":
        # Admin can see all tickets
        return db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    elif user.role == "technician":
        # Technician can see unassigned tickets and tickets assigned to them
        return db.query(Ticket).filter(
            or_(
                Ticket.assigned_to == user.id,
                Ticket.assigned_to.is_(None)
            )
        ).order_by(Ticket.created_at.desc()).all()
    else:
        # Regular user can only see their own tickets
        return db.query(Ticket).filter(
            Ticket.created_by == user.id
        ).order_by(Ticket.created_at.desc()).all()


def get_ticket_by_id(db: Session, ticket_id: int, user: User) -> Optional[Ticket]:
    """Get ticket by ID with permission check"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        return None
    
    # Check permissions
    if user.role == "admin":
        return ticket
    elif user.role == "technician":
        if ticket.assigned_to == user.id or ticket.assigned_to is None:
            return ticket
    else:
        if ticket.created_by == user.id:
            return ticket
    
    return None


def update_ticket(db: Session, ticket_id: int, ticket_update: TicketUpdate, user: User) -> Optional[Ticket]:
    """Update ticket with permission checks"""
    ticket = get_ticket_by_id(db, ticket_id, user)
    if not ticket:
        return None
    
    # Permission checks for different updates
    if user.role == "user":
        # Users can only update title/description of their own unassigned tickets
        if ticket.assigned_to is not None:
            return None
        if ticket_update.title is not None:
            ticket.title = ticket_update.title
        if ticket_update.description is not None:
            ticket.description = ticket_update.description
        if ticket_update.priority is not None:
            ticket.priority = ticket_update.priority
    elif user.role == "technician":
        # Technicians can claim tickets, update status, but not close
        if ticket_update.assigned_to == user.id and ticket.assigned_to is None:
            ticket.assigned_to = user.id
        if ticket_update.status and ticket_update.status != "closed":
            if ticket.assigned_to == user.id or ticket.assigned_to is None:
                ticket.status = ticket_update.status
        if ticket_update.priority is not None:
            ticket.priority = ticket_update.priority
    elif user.role == "admin":
        # Admin can update everything
        if ticket_update.title is not None:
            ticket.title = ticket_update.title
        if ticket_update.description is not None:
            ticket.description = ticket_update.description
        if ticket_update.status is not None:
            ticket.status = ticket_update.status
        if ticket_update.priority is not None:
            ticket.priority = ticket_update.priority
        if ticket_update.assigned_to is not None:
            ticket.assigned_to = ticket_update.assigned_to
    
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def add_ticket_note(db: Session, ticket_id: int, note: TicketNoteCreate, user: User) -> Optional[TicketNote]:
    """Add a note to a ticket"""
    ticket = get_ticket_by_id(db, ticket_id, user)
    if not ticket:
        return None
    
    # Permission check for internal notes
    if note.is_internal and user.role == "user":
        return None
    
    db_note = TicketNote(
        ticket_id=ticket_id,
        author_id=user.id,
        body=note.body,
        is_internal=note.is_internal
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_unassigned_tickets(db: Session) -> List[Ticket]:
    """Get all unassigned tickets"""
    return db.query(Ticket).filter(
        Ticket.assigned_to.is_(None),
        Ticket.status != "closed"
    ).order_by(Ticket.created_at.desc()).all()


def get_assigned_tickets(db: Session, user_id: int) -> List[Ticket]:
    """Get tickets assigned to a specific user"""
    return db.query(Ticket).filter(
        Ticket.assigned_to == user_id
    ).order_by(Ticket.created_at.desc()).all()
