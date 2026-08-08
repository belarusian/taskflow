"""Notification models for TaskFlow."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class NotificationType(str, Enum):
    """Types of notifications."""

    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_STATUS_CHANGED = "ticket.status_changed"
    TICKET_COMMENT = "ticket.comment"
    TICKET_CREATED = "ticket.created"
    TICKET_PRIORITY_CHANGED = "ticket.priority_changed"
    TICKET_DELETED = "ticket.deleted"
    LABEL_ADDED = "label.added"
    LABEL_REMOVED = "label.removed"
    MENTION = "mention"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Notification:
    """Represents a notification."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.SYSTEM
    title: str = ""
    message: str = ""
    recipient: Optional[str] = None
    sender: Optional[str] = None
    ticket_id: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    read: bool = False
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "recipient": self.recipient,
            "sender": self.sender,
            "ticket_id": self.ticket_id,
            "priority": self.priority.value,
            "read": self.read,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Notification:
        """Create notification from dictionary."""
        if "type" in data and isinstance(data["type"], str):
            data["type"] = NotificationType(data["type"])
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = NotificationPriority(data["priority"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def __str__(self) -> str:
        """String representation of notification."""
        status = "🔴" if not self.read else "🔵"
        return f"{status} [{self.type.value}] {self.title}: {self.message}"
