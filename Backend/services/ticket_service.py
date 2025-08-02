import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
from models.ticket_models import TicketCreate, TicketUpdate, Ticket

class TicketService:
    def __init__(self, data_dir: str = "storage/tickets"):
        self.data_dir = data_dir
        self.tickets_file = os.path.join(data_dir, "tickets.json")
        os.makedirs(data_dir, exist_ok=True)

    def load_tickets(self) -> List[dict]:
        """Load tickets from JSON file"""
        if os.path.exists(self.tickets_file):
            with open(self.tickets_file, 'r') as f:
                return json.load(f)
        return []

    def save_tickets(self, tickets: List[dict]) -> None:
        """Save tickets to JSON file"""
        with open(self.tickets_file, 'w') as f:
            json.dump(tickets, f, indent=2)

    def get_all_tickets(self) -> List[dict]:
        """Get all tickets"""
        return self.load_tickets()

    def get_ticket_by_id(self, ticket_id: str) -> Optional[dict]:
        """Get a specific ticket by ID"""
        tickets = self.load_tickets()
        return next((t for t in tickets if t["id"] == ticket_id), None)

    def create_ticket(self, ticket_data: TicketCreate) -> dict:
        """Create a new ticket"""
        tickets = self.load_tickets()
        new_ticket = {
            "id": str(uuid.uuid4()),
            "title": ticket_data.title,
            "description": ticket_data.description,
            "priority": ticket_data.priority,
            "status": ticket_data.status,
            "assignee": ticket_data.assignee,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        tickets.append(new_ticket)
        self.save_tickets(tickets)
        return new_ticket

    def update_ticket(self, ticket_id: str, updates: TicketUpdate) -> Optional[dict]:
        """Update an existing ticket"""
        tickets = self.load_tickets()
        ticket = next((t for t in tickets if t["id"] == ticket_id), None)
        
        if not ticket:
            return None
        
        # Handle both Pydantic v1 and v2
        try:
            # Pydantic v2
            update_data = updates.model_dump(exclude_unset=True)
        except AttributeError:
            # Pydantic v1
            update_data = updates.dict(exclude_unset=True)
            
        for key, value in update_data.items():
            ticket[key] = value
        
        ticket["updated_at"] = datetime.now().isoformat()
        self.save_tickets(tickets)
        return ticket

    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket"""
        tickets = self.load_tickets()
        ticket = next((t for t in tickets if t["id"] == ticket_id), None)
        
        if not ticket:
            return False
        
        tickets.remove(ticket)
        self.save_tickets(tickets)
        return True

    def find_ticket_by_partial_id(self, partial_id: str) -> Optional[dict]:
        """Find ticket by partial ID (used in function calling)"""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == partial_id or ticket["id"].startswith(partial_id):
                return ticket
        return None

    def get_filtered_tickets(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[dict]:
        """Get tickets filtered by status and/or priority"""
        tickets = self.load_tickets()
        
        if status:
            tickets = [t for t in tickets if t["status"] == status]
        if priority:
            tickets = [t for t in tickets if t["priority"] == priority]
        
        return tickets 