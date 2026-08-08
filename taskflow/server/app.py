"""FastAPI application for TaskFlow server."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from taskflow.server.config import ServerConfig
from taskflow.server.notification_engine import NotificationEngine
from taskflow.server.websocket_manager import WebSocketManager
from taskflow.services.ticket_service import TicketService
from taskflow.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def create_app(config: ServerConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = ServerConfig()

    app = FastAPI(
        title="TaskFlow Server",
        description="Real-time collaboration server for TaskFlow",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize managers
    ws_manager = WebSocketManager()
    notification_engine = NotificationEngine(ws_manager)
    ticket_service = TicketService()
    notification_service = NotificationService()

    # Store references for use in routes
    app.state.ws_manager = ws_manager
    app.state.notification_engine = notification_engine
    app.state.ticket_service = ticket_service
    app.state.notification_service = notification_service
    app.state.config = config

    # Register default event handlers
    _register_default_handlers(notification_engine)

    # WebSocket endpoint
    @app.websocket(config.ws_path)
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """Handle WebSocket connections."""
        connection = await ws_manager.connect(websocket, "anonymous")
        username = connection.username

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type", "")

                if msg_type == "auth":
                    username = message.get("username", "anonymous")
                    connection.username = username
                    await notification_engine.emit_user_event(
                        "connected", username, {"status": "online"}
                    )
                elif msg_type == "subscribe":
                    event = message.get("event", "")
                    await ws_manager.subscribe(connection.connection_id, event)
                    await connection.send_json({
                        "type": "subscribed",
                        "event": event,
                    })
                elif msg_type == "unsubscribe":
                    event = message.get("event", "")
                    await ws_manager.unsubscribe(connection.connection_id, event)
                elif msg_type == "ping":
                    await connection.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                elif msg_type == "message":
                    # Relay messages to other users
                    await ws_manager.broadcast({
                        "type": "message",
                        "from": username,
                        "content": message.get("content", ""),
                        "timestamp": datetime.utcnow().isoformat(),
                    }, exclude=connection.connection_id)
                else:
                    await connection.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })
        except WebSocketDisconnect:
            await ws_manager.disconnect(connection.connection_id)
            await notification_engine.emit_user_event(
                "disconnected", username, {"status": "offline"}
            )
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await ws_manager.disconnect(connection.connection_id)

    # API routes
    @app.get(f"{config.api_prefix}/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "connections": ws_manager.get_connection_count(),
            "users": ws_manager.get_user_count(),
        }

    @app.get(f"{config.api_prefix}/status")
    async def server_status() -> dict:
        """Get detailed server status."""
        return {
            "server": config.to_dict(),
            "websocket": await ws_manager.get_status(),
            "notifications": notification_engine.get_status(),
        }

    @app.get(f"{config.api_prefix}/tickets")
    async def api_list_tickets() -> list[dict]:
        """List all tickets via API."""
        tickets = ticket_service.list_tickets()
        return [t.model_dump() for t in tickets]

    @app.post(f"{config.api_prefix}/tickets")
    async def api_create_ticket(title: str, description: str = "", priority: str = "medium") -> dict:
        """Create a ticket via API."""
        ticket = ticket_service.create_ticket(title=title, description=description, priority=priority)
        await notification_engine.emit_ticket_event(
            NotificationType.TICKET_CREATED,
            ticket.model_dump(),
        )
        return ticket.model_dump()

    @app.get(f"{config.api_prefix}/online-users")
    async def api_online_users() -> list[str]:
        """Get list of online users."""
        return ws_manager.get_online_users()

    @app.post(f"{config.api_prefix}/notifications/broadcast")
    async def api_broadcast(message: dict[str, Any]) -> dict:
        """Broadcast a notification to all connected clients."""
        count = await ws_manager.broadcast(message)
        return {"sent_to": count}

    return app


def _register_default_handlers(engine: NotificationEngine) -> None:
    """Register default event handlers."""

    async def on_ticket_created(event: dict) -> None:
        logger.info(f"Ticket created: {event.get('data', {}).get('ticket', {}).get('title')}")

    async def on_user_connected(event: dict) -> None:
        username = event.get("data", {}).get("username")
        logger.info(f"User connected: {username}")

    engine.on("ticket.ticket_created", on_ticket_created)
    engine.on("user.connected", on_user_connected)
