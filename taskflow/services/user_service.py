"""User service with business logic for user management."""

from __future__ import annotations

from typing import Optional

from taskflow.models.user import User
from taskflow.storage.user_store import UserStore


class UserService:
    """Service layer for user operations."""

    def __init__(self, store: Optional[UserStore] = None) -> None:
        """Initialize with optional store instance."""
        self.store = store or UserStore()

    def create_user(
        self,
        username: str,
        email: str = "",
        display_name: str = "",
    ) -> User:
        """Create a new user."""
        if self.store.exists(username):
            raise ValueError(f"User '{username}' already exists")
        user = User(
            username=username,
            email=email,
            display_name=display_name,
        )
        return self.store.create(user)

    def get_user(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.store.get(username)

    def update_user(
        self,
        username: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        """Update user details."""
        user = self.store.get(username)
        if user is None:
            return None
        if email is not None:
            user.email = email
        if display_name is not None:
            user.display_name = display_name
        if is_active is not None:
            user.is_active = is_active
        return self.store.update(user)

    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        return self.store.delete(username)

    def list_users(self, active_only: bool = False) -> list[User]:
        """List users with optional active filter."""
        if active_only:
            return self.store.get_active()
        return self.store.list_all()

    def get_online_users(self) -> list[User]:
        """Get currently online users."""
        return self.store.get_online()

    def track_connection(self, username: str, connected: bool = True) -> None:
        """Track user connection status."""
        user = self.store.get(username)
        if user is None:
            return
        if connected:
            user.increment_clients()
        else:
            user.decrement_clients()
        self.store.update(user)
