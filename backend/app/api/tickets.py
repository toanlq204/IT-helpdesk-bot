from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.user import User
from ..schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketNoteCreate, TicketNoteResponse
from ..utils.auth import get_current_user
from ..services.ticket_service import (
    create_ticket, get_tickets_for_user, get_ticket_by_id,
    update_ticket, add_ticket_note, get_unassigned_tickets, get_assigned_tickets
)

router = APIRouter()


@router.post("/", response_model=TicketResponse)
async def create_new_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ticket"""
    return create_ticket(db, ticket, current_user.id)


@router.get("/", response_model=List[TicketResponse])
async def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tickets based on user role"""
    return get_tickets_for_user(db, current_user)


@router.get("/unassigned", response_model=List[TicketResponse])
async def list_unassigned_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List unassigned tickets (technician/admin only)"""
    if current_user.role not in ["technician", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return get_unassigned_tickets(db)


@router.get("/assigned", response_model=List[TicketResponse])
async def list_assigned_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tickets assigned to current user (technician/admin only)"""
    if current_user.role not in ["technician", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return get_assigned_tickets(db, current_user.id)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ticket details"""
    ticket = get_ticket_by_id(db, ticket_id, current_user)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or access denied"
        )
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket_endpoint(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ticket"""
    ticket = update_ticket(db, ticket_id, ticket_update, current_user)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or update not allowed"
        )
    return ticket


@router.post("/{ticket_id}/notes", response_model=TicketNoteResponse)
async def add_note_to_ticket(
    ticket_id: int,
    note: TicketNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a note to a ticket"""
    ticket_note = add_ticket_note(db, ticket_id, note, current_user)
    if not ticket_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or note creation not allowed"
        )
    return ticket_note
