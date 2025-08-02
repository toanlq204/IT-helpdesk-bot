from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.ticket_models import TicketCreate, TicketUpdate, Ticket
from services.ticket_service import TicketService

router = APIRouter()

# Dependency injection
def get_ticket_service():
    return TicketService()

@router.get("/tickets", response_model=List[dict])
async def get_tickets(ticket_service: TicketService = Depends(get_ticket_service)):
    """Get all tickets"""
    return ticket_service.get_all_tickets()

@router.post("/tickets", response_model=dict)
async def create_ticket(
    ticket: TicketCreate,
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Create a new ticket"""
    return ticket_service.create_ticket(ticket)

@router.get("/tickets/{ticket_id}", response_model=dict)
async def get_ticket(
    ticket_id: str,
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Get a specific ticket by ID"""
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.put("/tickets/{ticket_id}", response_model=dict)
async def update_ticket(
    ticket_id: str,
    updates: TicketUpdate,
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Update an existing ticket"""
    ticket = ticket_service.update_ticket(ticket_id, updates)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.delete("/tickets/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Delete a ticket"""
    success = ticket_service.delete_ticket(ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted successfully"}