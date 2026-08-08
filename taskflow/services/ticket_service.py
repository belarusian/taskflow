"""Ticket service with business logic for ticket operations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from taskflow.models.ticket import Priority, Status, Ticket
from taskflow.storage.ticket_store import TicketStore


class TicketService:
    """Service layer for ticket operations with validation."""

    def __init__(self, store: Optional[TicketStore] = None) -> None:
        """Initialize with optional store instance."""
        self.store = store or TicketStore()

    def create_ticket(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        assignee: Optional[str] = None,
        reporter: Optional[str] = None,
        labels: Optional[list[str]] = None,
        due_date: Optional[str] = None,
    ) -> Ticket:
        """Create a new ticket with validation."""
        ticket = Ticket(
            title=title,
            description=description,
            priority=Priority.from_string(priority),
            assignee=assignee,
            reporter=reporter,
            labels=labels or [],
        )
        if due_date:
            ticket.due_date = datetime.fromisoformat(due_date)
        return self.store.create(ticket)

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID."""
        return self.store.get(ticket_id)

    def update_ticket(
        self,
        ticket_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Optional[Ticket]:
        """Update an existing ticket."""
        ticket = self.store.get(ticket_id)
        if ticket is None:
            return None

        if title is not None:
            ticket.title = title
        if description is not None:
            ticket.description = description
        if priority is not None:
            ticket.priority = Priority.from_string(priority)
        if status is not None:
            ticket.update_status(Status.from_string(status))
        if assignee is not None:
            ticket.assign_to(assignee)
        if assignee == "":
            ticket.unassign()

        return self.store.update(ticket)

    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket."""
        return self.store.delete(ticket_id)

    def add_label(self, ticket_id: str, label: str) -> Optional[Ticket]:
        """Add a label to a ticket."""
        ticket = self.store.get(ticket_id)
        if ticket is None:
            return None
        ticket.add_label(label)
        return self.store.update(ticket)

    def remove_label(self, ticket_id: str, label: str) -> Optional[Ticket]:
        """Remove a label from a ticket."""
        ticket = self.store.get(ticket_id)
        if ticket is None:
            return None
        ticket.remove_label(label)
        return self.store.update(ticket)

    def assign_ticket(self, ticket_id: str, assignee: str) -> Optional[Ticket]:
        """Assign a ticket to a user."""
        ticket = self.store.get(ticket_id)
        if ticket is None:
            return None
        ticket.assign_to(assignee)
        return self.store.update(ticket)

    def unassign_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Remove assignee from a ticket."""
        ticket = self.store.get(ticket_id)
        if ticket is None:
            return None
        ticket.unassign()
        return self.store.update(ticket)

    def change_status(self, ticket_id: str, status: str) -> Optional[Ticket]:
        """Change ticket status."""
        ticket = self.store.get(ticket_id)
        if ticket is None:
            return None
        ticket.update_status(Status.from_string(status))
        return self.store.update(ticket)

    def list_tickets(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        label: Optional[str] = None,
    ) -> list[Ticket]:
        """List tickets with optional filters."""
        tickets = self.store.list_all()

        if status:
            tickets = [t for t in tickets if t.status == Status.from_string(status)]
        if priority:
            tickets = [t for t in tickets if t.priority == Priority.from_string(priority)]
        if assignee:
            tickets = [t for t in tickets if t.assignee == assignee]
        if label:
            tickets = [t for t in tickets if label in t.labels]

        return tickets

    def search_tickets(self, query: str) -> list[Ticket]:
        """Search tickets by text."""
        return self.store.search(query)

    def get_stats(self) -> dict:
        """Get ticket statistics."""
        tickets = self.store.list_all()
        stats: dict = {"total": len(tickets)}
        for status in Status:
            stats[status.value] = sum(
                1 for t in tickets if t.status == status
            )
        for priority in Priority:
            stats[f"priority_{priority.value}"] = sum(
                1 for t in tickets if t.priority == priority
            )
        stats["unassigned"] = sum(1 for t in tickets if t.assignee is None)
        stats["overdue"] = sum(1 for t in tickets if t.is_overdue())
        return stats
