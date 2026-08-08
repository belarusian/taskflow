"""WebSocket manager for real-time collaboration."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a single WebSocket connection."""

    def __init__(self, websocket: Any, username: str) -> None:
        """Initialize connection.

        Args:
            websocket: The WebSocket connection object.
            username: Username associated with this connection.
        """
        self.websocket = websocket
        self.username = username
        self.connected_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.subscriptions: set[str] = set()

    async def send(self, data: dict[str, Any]) -> None:
        """Send data to this connection.

        Args:
            data: Dictionary to send as JSON.
        """
        try:
            await self.websocket.send(json.dumps(data))
            self.last_activity = datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"Error sending to {self.username}: {e}")

    def is_expired(self, timeout: int = 300) -> bool:
        """Check if connection has been inactive too long.

        Args:
            timeout: Seconds of inactivity before expiry.

        Returns:
            True if connection is expired.
        """
        elapsed = (datetime.now(timezone.utc) - self.last_activity).total_seconds()
        return elapsed > timeout


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        """Initialize the manager."""
        self._connections: dict[str, WebSocketConnection] = {}
        self._subscribers: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def register(self, websocket: Any, username: str) -> None:
        """Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection object.
            username: Username for this connection.
        """
        async with self._lock:
            conn = WebSocketConnection(websocket, username)
            self._connections[username] = conn
            logger.info(f"User {username} connected")

    async def unregister(self, username: str) -> None:
        """Remove a WebSocket connection.

        Args:
            username: Username to disconnect.
        """
        async with self._lock:
            if username in self._connections:
                conn = self._connections.pop(username)
                # Remove from all subscriptions
                for subs in self._subscribers.values():
                    subs.discard(username)
                logger.info(f"User {username} disconnected")

    async def subscribe(self, username: str, event_type: str) -> None:
        """Subscribe a user to an event type.

        Args:
            username: Username to subscribe.
            event_type: Event type to subscribe to.
        """
        async with self._lock:
            if username not in self._subscribers:
                self._subscribers[username] = set()
            self._subscribers[username].add(event_type)
            if event_type not in self._subscribers:
                self._subscribers[event_type] = set()
            self._subscribers[event_type].add(username)
            logger.debug(f"User {username} subscribed to {event_type}")

    async def unsubscribe(self, username: str, event_type: str) -> None:
        """Unsubscribe a user from an event type.

        Args:
            username: Username to unsubscribe.
            event_type: Event type to unsubscribe from.
        """
        async with self._lock:
            if username in self._subscribers:
                self._subscribers[username].discard(event_type)
            if event_type in self._subscribers:
                self._subscribers[event_type].discard(username)

    async def broadcast(self, data: dict[str, Any]) -> int:
        """Broadcast data to all connected users.

        Args:
            data: Dictionary to broadcast.

        Returns:
            Number of users who received the message.
        """
        sent = 0
        async with self._lock:
            for username, conn in list(self._connections.items()):
                await conn.send(data)
                sent += 1
        return sent

    async def broadcast_to_subscribers(self, event_type: str, data: dict[str, Any]) -> int:
        """Broadcast to users subscribed to an event type.

        Args:
            event_type: Event type to match subscriptions.
            data: Dictionary to broadcast.

        Returns:
            Number of subscribers who received the message.
        """
        sent = 0
        async with self._lock:
            subscribers = self._subscribers.get(event_type, set())
            for username in subscribers:
                if username in self._connections:
                    await self._connections[username].send(data)
                    sent += 1
        return sent

    async def send_to_user(self, username: str, data: dict[str, Any]) -> bool:
        """Send data to a specific user.

        Args:
            username: Username to send to.
            data: Dictionary to send.

        Returns:
            True if message was sent successfully.
        """
        async with self._lock:
            if username in self._connections:
                await self._connections[username].send(data)
                return True
        return False

    def get_connected_users(self) -> list[str]:
        """Get list of connected usernames.

        Returns:
            List of connected usernames.
        """
        return list(self._connections.keys())

    def get_connection_count(self) -> int:
        """Get number of active connections.

        Returns:
            Number of active connections.
        """
        return len(self._connections)

    async def cleanup_expired(self, timeout: int = 300) -> int:
        """Remove expired connections.

        Args:
            timeout: Seconds of inactivity before expiry.

        Returns:
            Number of connections removed.
        """
        removed = 0
        async with self._lock:
            expired = [
                username for username, conn in self._connections.items()
                if conn.is_expired(timeout)
            ]
            for username in expired:
                await self.unregister(username)
                removed += 1
        return removed

    def get_status(self) -> dict:
        """Get manager status.

        Returns:
            Dictionary with status information.
        """
        return {
            "connected_users": len(self._connections),
            "subscriptions": {
                k: len(v) for k, v in self._subscribers.items()
            },
        }
