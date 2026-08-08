"""User model for assignees and reporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Represents a user in the TaskFlow system."""

    username: str
    email: str = ""
    display_name: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    connected_clients: int = field(default=0)

    def __post_init__(self) -> None:
        """Validate and normalize user data."""
        if not self.username or not self.username.strip():
            raise ValueError("Username cannot be empty")
        self.username = self.username.strip().lower()
        if not self.display_name:
            self.display_name = self.username.replace("-", " ").title()

    def mark_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen = datetime.utcnow()

    def increment_clients(self) -> None:
        """Increment connected client count."""
        self.connected_clients += 1
        self.mark_seen()

    def decrement_clients(self) -> None:
        """Decrement connected client count."""
        self.connected_clients = max(0, self.connected_clients - 1)

    def __repr__(self) -> str:
        return f"User(username={self.username!r}, active={self.is_active})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.username == other.username
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.username)
