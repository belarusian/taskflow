"""Notification model for real-time collaboration alerts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NotificationType(str, Enum):
    """Types of notifications in the system."""

    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    TICKET_COMMENTED = "ticket_commented"
    TICKET_LABEL_ADDED = "ticket_label_added"
    TICKET_DELETED = "ticket_deleted"
    USER_MENTIONED = "user_mentioned"
    SYSTEM = "system"


class NotificationSeverity(str, Enum):
    """Severity levels for notifications."""

    INFO = "info"
    WARNING = "warning"
    IMPORTANT = "important"


@dataclass
class Notification:
    """Represents a notification sent to users."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: NotificationType = NotificationType.SYSTEM
    severity: NotificationSeverity = NotificationSeverity.INFO
    title: str = ""
    message: str = ""
    recipient: Optional[str] = None
    sender: Optional[str] = None
    ticket_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)

    def mark_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert notification to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "recipient": self.recipient,
            "sender": self.sender,
            "ticket_id": self.ticket_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_ticket_event(
        cls,
        event_type: NotificationType,
        ticket_id: str,
        message: str,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
    ) -> Notification:
        """Create a notification from a ticket event."""
        return cls(
            type=event_type,
            ticket_id=ticket_id,
            message=message,
            sender=sender,
            recipient=recipient,
            title=f"Ticket {ticket_id[:6]} - {event_type.value.replace('_', ' ')}",
        )

    def __repr__(self) -> str:
        return f"Notification(id={self.id}, type={self.type.value}, read={self.is_read})"
