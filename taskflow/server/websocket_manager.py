"""WebSocket connection manager for real-time collaboration."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class Connection:
    """Represents a single WebSocket connection."""

    def __init__(self, websocket: WebSocket, username: str, connection_id: str) -> None:
        """Initialize a connection."""
        self.websocket = websocket
        self.username = username
        self.connection_id = connection_id
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_connected = True
        self.subscribed_events: set[str] = set()

    async def send_json(self, data: dict[str, Any]) -> None:
        """Send JSON data to the connection."""
        if self.is_connected:
            try:
                await self.websocket.send_json(data)
                self.last_activity = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error sending to {self.connection_id}: {e}")
                self.is_connected = False

    async def send_text(self, text: str) -> None:
        """Send text data to the connection."""
        if self.is_connected:
            try:
                await self.websocket.send_text(text)
                self.last_activity = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error sending to {self.connection_id}: {e}")
                self.is_connected = False

    def to_dict(self) -> dict:
        """Convert connection to dictionary."""
        return {
            "connection_id": self.connection_id,
            "username": self.username,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_connected": self.is_connected,
            "subscribed_events": list(self.subscribed_events),
        }


class WebSocketManager:
    """Manages all WebSocket connections and message broadcasting."""

    def __init__(self) -> None:
        """Initialize the WebSocket manager."""
        self.connections: dict[str, Connection] = {}
        self.user_connections: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, username: str) -> Connection:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        connection_id = f"{username}_{id(websocket)}"
        connection = Connection(websocket, username, connection_id)

        async with self._lock:
            self.connections[connection_id] = connection
            if username not in self.user_connections:
                self.user_connections[username] = []
            self.user_connections[username].append(connection_id)

        logger.info(f"User {username} connected ({connection_id})")
        await connection.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return connection

    async def disconnect(self, connection_id: str) -> None:
        """Handle a WebSocket disconnection."""
        async with self._lock:
            connection = self.connections.pop(connection_id, None)
            if connection:
                connection.is_connected = False
                if connection.username in self.user_connections:
                    if connection_id in self.user_connections[connection.username]:
                        self.user_connections[connection.username].remove(connection_id)
                    if not self.user_connections[connection.username]:
                        del self.user_connections[connection.username]
                logger.info(f"User {connection.username} disconnected ({connection_id})")

    async def broadcast(self, message: dict[str, Any], exclude: Optional[str] = None) -> int:
        """Broadcast a message to all connected clients."""
        sent_count = 0
        for conn_id, connection in list(self.connections.items()):
            if exclude and conn_id == exclude:
                continue
            if connection.is_connected:
                await connection.send_json(message)
                sent_count += 1
        return sent_count

    async def send_to_user(self, username: str, message: dict[str, Any]) -> int:
        """Send a message to all connections of a specific user."""
        sent_count = 0
        if username in self.user_connections:
            for conn_id in self.user_connections[username]:
                connection = self.connections.get(conn_id)
                if connection and connection.is_connected:
                    await connection.send_json(message)
                    sent_count += 1
        return sent_count

    async def send_to_connection(self, connection_id: str, message: dict[str, Any]) -> bool:
        """Send a message to a specific connection."""
        connection = self.connections.get(connection_id)
        if connection and connection.is_connected:
            await connection.send_json(message)
            return True
        return False

    async def subscribe(self, connection_id: str, event_type: str) -> None:
        """Subscribe a connection to an event type."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscribed_events.add(event_type)
            logger.info(f"Connection {connection_id} subscribed to {event_type}")

    async def unsubscribe(self, connection_id: str, event_type: str) -> None:
        """Unsubscribe a connection from an event type."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscribed_events.discard(event_type)

    async def broadcast_to_subscribers(self, event_type: str, message: dict[str, Any]) -> int:
        """Broadcast to connections subscribed to a specific event type."""
        sent_count = 0
        for connection in self.connections.values():
            if connection.is_connected and event_type in connection.subscribed_events:
                await connection.send_json(message)
                sent_count += 1
        return sent_count

    def get_active_connections(self) -> list[Connection]:
        """Get all active connections."""
        return [c for c in self.connections.values() if c.is_connected]

    def get_user_count(self) -> int:
        """Get count of unique connected users."""
        return len(self.user_connections)

    def get_connection_count(self) -> int:
        """Get total connection count."""
        return len(self.connections)

    def is_user_online(self, username: str) -> bool:
        """Check if a user has active connections."""
        return username in self.user_connections and bool(
            self.user_connections[username]
        )

    def get_online_users(self) -> list[str]:
        """Get list of online usernames."""
        return list(self.user_connections.keys())

    async def get_status(self) -> dict:
        """Get manager status for health checks."""
        return {
            "total_connections": self.get_connection_count(),
            "unique_users": self.get_user_count(),
            "online_users": self.get_online_users(),
            "connections": [
                c.to_dict() for c in self.get_active_connections()
            ],
        }
