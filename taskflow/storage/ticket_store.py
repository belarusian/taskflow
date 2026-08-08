"""Ticket storage with CRUD operations and filtering."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from taskflow.models.ticket import Priority, Status, Ticket
from taskflow.storage.file_store import FileStore


class TicketStore(FileStore):
    """Persistent storage for tickets with filtering support."""

    TICKETS_FILE = "tickets.json"

    def _load_tickets(self) -> dict[str, dict]:
        """Load all tickets from storage."""
        data = self._read_json(self.TICKETS_FILE)
        return data if isinstance(data, dict) else {}

    def _save_tickets(self, tickets: dict[str, dict]) -> None:
        """Save all tickets to storage."""
        self._write_json(self.TICKETS_FILE, tickets)

    def create(self, ticket: Ticket) -> Ticket:
        """Create and persist a new ticket."""
        tickets = self._load_tickets()
        tickets[ticket.id] = ticket.model_dump()
        self._save_tickets(tickets)
        return ticket

    def get(self, ticket_id: str) -> Optional[Ticket]:
        """Retrieve a ticket by ID."""
        tickets = self._load_tickets()
        data = tickets.get(ticket_id)
        if data is None:
            return None
        return Ticket(**data)

    def update(self, ticket: Ticket) -> Optional[Ticket]:
        """Update an existing ticket."""
        tickets = self._load_tickets()
        if ticket.id not in tickets:
            return None
        ticket.updated_at = datetime.utcnow()
        tickets[ticket.id] = ticket.model_dump()
        self._save_tickets(tickets)
        return ticket

    def delete(self, ticket_id: str) -> bool:
        """Delete a ticket by ID."""
        tickets = self._load_tickets()
        if ticket_id not in tickets:
            return False
        del tickets[ticket_id]
        self._save_tickets(tickets)
        return True

    def list_all(self) -> list[Ticket]:
        """List all tickets."""
        tickets = self._load_tickets()
        return [Ticket(**data) for data in tickets.values()]

    def filter_by_status(self, status: Status) -> list[Ticket]:
        """Filter tickets by status."""
        return [t for t in self.list_all() if t.status == status]

    def filter_by_priority(self, priority: Priority) -> list[Ticket]:
        """Filter tickets by priority."""
        return [t for t in self.list_all() if t.priority == priority]

    def filter_by_assignee(self, assignee: str) -> list[Ticket]:
        """Filter tickets by assignee."""
        return [t for t in self.list_all() if t.assignee == assignee]

    def filter_by_label(self, label: str) -> list[Ticket]:
        """Filter tickets by label."""
        return [t for t in self.list_all() if label in t.labels]

    def search(self, query: str) -> list[Ticket]:
        """Search tickets by title or description."""
        query_lower = query.lower()
        return [
            t for t in self.list_all()
            if query_lower in t.title.lower()
            or query_lower in t.description.lower()
        ]

    def count(self) -> int:
        """Count total number of tickets."""
        return len(self._load_tickets())

    def get_unassigned(self) -> list[Ticket]:
        """Get all unassigned tickets."""
        return [t for t in self.list_all() if t.assignee is None]

    def get_overdue(self) -> list[Ticket]:
        """Get all overdue tickets."""
        return [t for t in self.list_all() if t.is_overdue()]
