"""Core data models for TaskFlow."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    """Possible states for a ticket."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Priority levels for tickets."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Label(BaseModel):
    """A label that can be attached to tickets."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    color: str = "#000000"
    description: Optional[str] = None

    def __hash__(self):
        return hash(self.id)


class Ticket(BaseModel):
    """Represents a ticket/issue in the system."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    assignee: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    closed_at: Optional[datetime] = None
    creator: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert ticket to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "assignee": self.assignee,
            "labels": self.labels,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "creator": self.creator,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Ticket:
        """Create a Ticket instance from a dictionary."""
        if "status" in data and isinstance(data["status"], str):
            data["status"] = TicketStatus(data["status"])
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = TicketPriority(data["priority"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if "closed_at" in data and data["closed_at"] and isinstance(data["closed_at"], str):
            data["closed_at"] = datetime.fromisoformat(data["closed_at"])
        return cls(**data)
