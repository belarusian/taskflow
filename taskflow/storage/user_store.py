"""User storage for managing user accounts."""

from __future__ import annotations

from typing import Optional

from taskflow.models.user import User
from taskflow.storage.file_store import FileStore


class UserStore(FileStore):
    """Persistent storage for users."""

    USERS_FILE = "users.json"

    def _load_users(self) -> dict[str, dict]:
        """Load all users from storage."""
        data = self._read_json(self.USERS_FILE)
        return data if isinstance(data, dict) else {}

    def _save_users(self, users: dict[str, dict]) -> None:
        """Save all users to storage."""
        self._write_json(self.USERS_FILE, users)

    def create(self, user: User) -> User:
        """Create and persist a new user."""
        users = self._load_users()
        users[user.username] = user.__dict__
        self._save_users(users)
        return user

    def get(self, username: str) -> Optional[User]:
        """Retrieve a user by username."""
        users = self._load_users()
        data = users.get(username)
        if data is None:
            return None
        return User(**data)

    def update(self, user: User) -> Optional[User]:
        """Update an existing user."""
        users = self._load_users()
        if user.username not in users:
            return None
        users[user.username] = user.__dict__
        self._save_users(users)
        return user

    def delete(self, username: str) -> bool:
        """Delete a user by username."""
        users = self._load_users()
        if username not in users:
            return False
        del users[username]
        self._save_users(users)
        return True

    def list_all(self) -> list[User]:
        """List all users."""
        users = self._load_users()
        return [User(**data) for data in users.values()]

    def get_active(self) -> list[User]:
        """List all active users."""
        return [u for u in self.list_all() if u.is_active]

    def get_online(self) -> list[User]:
        """List users with active connections."""
        return [u for u in self.list_all() if u.connected_clients > 0]

    def exists(self, username: str) -> bool:
        """Check if a user exists."""
        return username in self._load_users()
