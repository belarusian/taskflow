"""In-memory ticket storage with persistence support."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from taskflow.models.ticket import Ticket, TicketStatus

logger = logging.getLogger(__name__)


class TicketStore:
    """Storage backend for tickets with file persistence."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize the ticket store.

        Args:
            storage_path: Optional path for JSON file persistence.
        """
        self._tickets: dict[str, Ticket] = {}
        self._storage_path = Path(storage_path) if storage_path else None
        if self._storage_path and self._storage_path.exists():
            self._load()

    def _load(self) -> None:
        """Load tickets from storage file."""
        try:
            data = json.loads(self._storage_path.read_text())
            for item in data:
                ticket = Ticket(**item)
                self._tickets[ticket.id] = ticket
            logger.info(f"Loaded {len(self._tickets)} tickets from storage")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load tickets: {e}")

    def _save(self) -> None:
        """Persist tickets to storage file."""
        if self._storage_path:
            data = [t.to_dict() for t in self._tickets.values()]
            self._storage_path.write_text(json.dumps(data, indent=2))

    def create(self, ticket: Ticket) -> Ticket:
        """Create a new ticket.

        Args:
            ticket: The ticket to create.

        Returns:
            The created ticket.
        """
        self._tickets[ticket.id] = ticket
        self._save()
        return ticket

    def get(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID.

        Args:
            ticket_id: The ticket ID.

        Returns:
            The ticket if found, None otherwise.
        """
        return self._tickets.get(ticket_id)

    def update(self, ticket: Ticket) -> Optional[Ticket]:
        """Update an existing ticket.

        Args:
            ticket: The ticket with updated fields.

        Returns:
            The updated ticket if it existed, None otherwise.
        """
        if ticket.id in self._tickets:
            ticket.updated_at = datetime.now(timezone.utc)
            self._tickets[ticket.id] = ticket
            self._save()
            return ticket
        return None

    def delete(self, ticket_id: str) -> bool:
        """Delete a ticket.

        Args:
            ticket_id: The ticket ID to delete.

        Returns:
            True if the ticket was deleted, False if not found.
        """
        if ticket_id in self._tickets:
            del self._tickets[ticket_id]
            self._save()
            return True
        return False

    def list_all(self) -> list[Ticket]:
        """List all tickets.

        Returns:
            List of all tickets.
        """
        return list(self._tickets.values())

    def list_by_status(self, status: TicketStatus) -> list[Ticket]:
        """List tickets by status.

        Args:
            status: The status to filter by.

        Returns:
            List of tickets with the given status.
        """
        return [t for t in self._tickets.values() if t.status == status]

    def list_by_assignee(self, assignee: str) -> list[Ticket]:
        """List tickets by assignee.

        Args:
            assignee: The assignee username.

        Returns:
            List of tickets assigned to the user.
        """
        return [t for t in self._tickets.values() if t.assignee == assignee]

    def list_by_label(self, label: str) -> list[Ticket]:
        """List tickets by label.

        Args:
            label: The label to filter by.

        Returns:
            List of tickets with the given label.
        """
        return [t for t in self._tickets.values() if label in t.labels]

    def get_overdue(self) -> list[Ticket]:
        """Get all overdue tickets.

        Returns:
            List of tickets past their due date.
        """
        now = datetime.now(timezone.utc)
        return [
            t for t in self._tickets.values()
            if t.due_date and t.due_date < now and t.status != TicketStatus.DONE
        ]

    def count(self) -> int:
        """Get total ticket count.

        Returns:
            Total number of tickets.
        """
        return len(self._tickets)

    def search(self, query: str) -> list[Ticket]:
        """Search tickets by title or description.

        Args:
            query: Search query string.

        Returns:
            List of matching tickets.
        """
        query_lower = query.lower()
        return [
            t for t in self._tickets.values()
            if query_lower in t.title.lower()
            or query_lower in (t.description or "").lower()
        ]
