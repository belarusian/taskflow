"""WebSocket message handlers for TaskFlow."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of WebSocket messages."""

    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_DELETED = "ticket.deleted"
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_STATUS_CHANGED = "ticket.status_changed"
    LABEL_ADDED = "label.added"
    LABEL_REMOVED = "label.removed"
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    NOTIFICATION = "notification"


@dataclass
class WebSocketMessage:
    """A WebSocket message."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sender: Optional[str] = None
    message_id: Optional[str] = None

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> WebSocketMessage:
        """Deserialize message from JSON string."""
        parsed = json.loads(data)
        return cls(
            type=parsed["type"],
            payload=parsed.get("payload", {}),
            timestamp=parsed.get("timestamp", ""),
            sender=parsed.get("sender"),
            message_id=parsed.get("message_id"),
        )

    @classmethod
    def from_dict(cls, data: dict) -> WebSocketMessage:
        """Create message from dictionary."""
        return cls(
            type=data["type"],
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", ""),
            sender=data.get("sender"),
            message_id=data.get("message_id"),
        )


class MessageHandler:
    """Handles incoming WebSocket messages and routes them."""

    def __init__(self):
        """Initialize the message handler."""
        self._handlers: dict[str, list] = {}
        self._subscribers: dict[str, set] = {}

    def register(self, message_type: str):
        """Decorator to register a handler for a message type.

        Args:
            message_type: The message type to handle.

        Returns:
            Decorator function.
        """
        def decorator(func):
            if message_type not in self._handlers:
                self._handlers[message_type] = []
            self._handlers[message_type].append(func)
            return func
        return decorator

    def subscribe(self, message_type: str, client_id: str) -> None:
        """Subscribe a client to a message type.

        Args:
            message_type: The message type to subscribe to.
            client_id: The client identifier.
        """
        if message_type not in self._subscribers:
            self._subscribers[message_type] = set()
        self._subscribers[message_type].add(client_id)
        logger.info(f"Client {client_id} subscribed to {message_type}")

    def unsubscribe(self, message_type: str, client_id: str) -> None:
        """Unsubscribe a client from a message type.

        Args:
            message_type: The message type to unsubscribe from.
            client_id: The client identifier.
        """
        if message_type in self._subscribers:
            self._subscribers[message_type].discard(client_id)
            logger.info(f"Client {client_id} unsubscribed from {message_type}")

    def get_subscribers(self, message_type: str) -> set[str]:
        """Get all subscribers for a message type.

        Args:
            message_type: The message type.

        Returns:
            Set of client IDs subscribed to the message type.
        """
        return self._subscribers.get(message_type, set()).copy()

    async def handle(self, message: WebSocketMessage, client_id: str) -> Optional[WebSocketMessage]:
        """Handle an incoming message.

        Args:
            message: The incoming message.
            client_id: The client that sent the message.

        Returns:
            Response message if applicable, None otherwise.
        """
        logger.debug(f"Handling message type={message.type} from client={client_id}")

        if message.type == MessageType.SUBSCRIBE:
            target_type = message.payload.get("type", "")
            self.subscribe(target_type, client_id)
            return WebSocketMessage(
                type=MessageType.PONG,
                payload={"subscribed": target_type},
                sender="server",
            )

        if message.type == MessageType.UNSUBSCRIBE:
            target_type = message.payload.get("type", "")
            self.unsubscribe(target_type, client_id)
            return WebSocketMessage(
                type=MessageType.PONG,
                payload={"unsubscribed": target_type},
                sender="server",
            )

        if message.type == MessageType.PING:
            return WebSocketMessage(
                type=MessageType.PONG,
                payload={"timestamp": datetime.now(timezone.utc).isoformat()},
                sender="server",
            )

        # Call registered handlers
        handlers = self._handlers.get(message.type, [])
        for handler in handlers:
            try:
                await handler(message, client_id)
            except Exception as e:
                logger.error(f"Handler error for {message.type}: {e}")
                return WebSocketMessage(
                    type=MessageType.ERROR,
                    payload={"error": str(e)},
                    sender="server",
                )

        return None
