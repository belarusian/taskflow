"""Ticket model with priority, status, labels, and assignee support."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str) -> Priority:
        """Create Priority from string, case-insensitive."""
        return cls(value.lower())


class Status(str, Enum):
    """Ticket lifecycle status."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, value: str) -> Status:
        """Create Status from string, case-insensitive."""
        return cls(value.lower())


class Ticket(BaseModel):
    """Represents a ticket/issue in the system."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=10000)
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    labels: list[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    parent_id: Optional[str] = None
    order: int = Field(default=0)

    def add_label(self, label: str) -> None:
        """Add a label if not already present."""
        if label not in self.labels:
            self.labels.append(label)
            self.updated_at = datetime.utcnow()

    def remove_label(self, label: str) -> None:
        """Remove a label if present."""
        if label in self.labels:
            self.labels.remove(label)
            self.updated_at = datetime.utcnow()

    def update_status(self, new_status: Status) -> None:
        """Update ticket status with timestamp."""
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def assign_to(self, user: str) -> None:
        """Assign ticket to a user."""
        self.assignee = user
        self.updated_at = datetime.utcnow()

    def unassign(self) -> None:
        """Remove assignee from ticket."""
        self.assignee = None
        self.updated_at = datetime.utcnow()

    def is_overdue(self) -> bool:
        """Check if ticket is past its due date."""
        if self.due_date is None:
            return False
        return datetime.utcnow() > self.due_date and self.status != Status.DONE

    def __repr__(self) -> str:
        return (
            f"Ticket(id={self.id}, title={self.title!r}, "
            f"priority={self.priority.value}, status={self.status.value})"
        )
