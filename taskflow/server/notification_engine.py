"""Notification engine for real-time event dispatch."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Optional

from taskflow.models.notification import Notification, NotificationType
from taskflow.server.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class NotificationEngine:
    """Engine for managing and dispatching real-time notifications."""

    def __init__(self, ws_manager: WebSocketManager) -> None:
        """Initialize with WebSocket manager."""
        self.ws_manager = ws_manager
        self._handlers: dict[str, list[Callable]] = {}
        self._event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def on(self, event_type: str, handler: Callable) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event: {event_type}")

    async def emit(self, event_type: str, data: dict[str, Any]) -> int:
        """Emit an event to all subscribers and handlers."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "server",
        }

        # Run registered handlers
        for handler in self._handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")

        # Broadcast to WebSocket subscribers
        sent = await self.ws_manager.broadcast_to_subscribers(event_type, event)

        # Also broadcast to all if no specific subscribers
        if sent == 0:
            await self.ws_manager.broadcast(event)

        return sent

    async def emit_ticket_event(
        self,
        event_type: NotificationType,
        ticket_data: dict[str, Any],
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
    ) -> int:
        """Emit a ticket-related event."""
        data = {
            "ticket": ticket_data,
            "sender": sender,
            "event_type": event_type.value,
        }

        # Send to specific recipient if provided
        if recipient:
            await self.ws_manager.send_to_user(recipient, {
                "type": "notification",
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            })

        # Broadcast to ticket event subscribers
        return await self.emit(f"ticket.{event_type.value}", data)

    async def emit_user_event(
        self,
        event_type: str,
        username: str,
        data: dict[str, Any],
    ) -> int:
        """Emit a user-related event."""
        data["username"] = username
        return await self.emit(f"user.{event_type}", data)

    async def emit_system_event(
        self,
        event_type: str,
        message: str,
        data: Optional[dict[str, Any]] = None,
    ) -> int:
        """Emit a system-wide event."""
        event_data = {"message": message, **(data or {})}
        return await self.emit(f"system.{event_type}", event_data)

    async def start(self) -> None:
        """Start the notification engine."""
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info("Notification engine started")

    async def stop(self) -> None:
        """Stop the notification engine."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Notification engine stopped")

    async def _process_queue(self) -> None:
        """Process queued events."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self.emit(event["type"], event["data"])
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")

    async def queue_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Queue an event for processing."""
        await self._event_queue.put({"type": event_type, "data": data})

    def get_status(self) -> dict:
        """Get engine status."""
        return {
            "running": self._running,
            "registered_handlers": {
                k: len(v) for k, v in self._handlers.items()
            },
            "queue_size": self._event_queue.qsize(),
        }
