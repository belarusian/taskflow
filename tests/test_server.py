"""Tests for TaskFlow server components."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from taskflow.server.config import ServerConfig
from taskflow.server.websocket_manager import WebSocketManager, Connection
from taskflow.server.notification_engine import NotificationEngine


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self) -> None:
        config = ServerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8765
        assert config.ws_path == "/ws"

    def test_custom_values(self) -> None:
        config = ServerConfig(host="0.0.0.0", port=9000)
        assert config.host == "0.0.0.0"
        assert config.port == 9000

    def test_get_ws_url(self) -> None:
        config = ServerConfig(host="localhost", port=8080)
        assert config.get_ws_url() == "ws://localhost:8080/ws"

    def test_get_api_url(self) -> None:
        config = ServerConfig(host="localhost", port=8080)
        assert config.get_api_url() == "http://localhost:8080/api"

    def test_to_dict(self) -> None:
        config = ServerConfig()
        data = config.to_dict()
        assert data["host"] == "127.0.0.1"
        assert data["port"] == 8765
        assert "max_connections" in data


class TestWebSocketManager:
    """Tests for WebSocketManager."""

    @pytest.fixture
    def manager(self) -> WebSocketManager:
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self) -> MagicMock:
        ws = MagicMock(spec=AsyncMock)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        assert conn.username == "alice"
        assert conn.is_connected is True
        assert manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        await manager.disconnect(conn.connection_id)
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        count = await manager.broadcast({"type": "test", "data": "hello"})
        assert count == 1

    @pytest.mark.asyncio
    async def test_broadcast_exclude(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        count = await manager.broadcast({"type": "test"}, exclude=conn.connection_id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        count = await manager.send_to_user("alice", {"type": "test"})
        assert count == 1

    @pytest.mark.asyncio
    async def test_send_to_user_not_found(self, manager: WebSocketManager) -> None:
        count = await manager.send_to_user("nonexistent", {"type": "test"})
        assert count == 0

    @pytest.mark.asyncio
    async def test_subscribe(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        await manager.subscribe(conn.connection_id, "ticket.created")
        assert "ticket.created" in conn.subscribed_events

    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        await manager.subscribe(conn.connection_id, "ticket.created")
        await manager.unsubscribe(conn.connection_id, "ticket.created")
        assert "ticket.created" not in conn.subscribed_events

    @pytest.mark.asyncio
    async def test_broadcast_to_subscribers(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        conn = await manager.connect(mock_websocket, "alice")
        await manager.subscribe(conn.connection_id, "ticket.created")
        count = await manager.broadcast_to_subscribers("ticket.created", {"data": "test"})
        assert count == 1

    @pytest.mark.asyncio
    async def test_is_user_online(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        await manager.connect(mock_websocket, "alice")
        assert manager.is_user_online("alice") is True
        assert manager.is_user_online("bob") is False

    @pytest.mark.asyncio
    async def test_get_online_users(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        await manager.connect(mock_websocket, "alice")
        users = manager.get_online_users()
        assert "alice" in users

    @pytest.mark.asyncio
    async def test_get_status(self, manager: WebSocketManager, mock_websocket: MagicMock) -> None:
        await manager.connect(mock_websocket, "alice")
        status = await manager.get_status()
        assert status["total_connections"] == 1
        assert status["unique_users"] == 1


class TestConnection:
    """Tests for Connection class."""

    def test_connection_creation(self) -> None:
        ws = MagicMock()
        conn = Connection(ws, "alice", "conn1")
        assert conn.username == "alice"
        assert conn.connection_id == "conn1"
        assert conn.is_connected is True

    def test_to_dict(self) -> None:
        ws = MagicMock()
        conn = Connection(ws, "alice", "conn1")
        data = conn.to_dict()
        assert data["username"] == "alice"
        assert data["connection_id"] == "conn1"
        assert "connected_at" in data


class TestNotificationEngine:
    """Tests for NotificationEngine."""

    @pytest.fixture
    def engine(self) -> NotificationEngine:
        ws_manager = WebSocketManager()
        return NotificationEngine(ws_manager)

    def test_register_handler(self, engine: NotificationEngine) -> None:
        handler_called = []

        def handler(event: dict) -> None:
            handler_called.append(event)

        engine.on("test.event", handler)
        assert "test.event" in engine._handlers

    @pytest.mark.asyncio
    async def test_emit(self, engine: NotificationEngine) -> None:
        received = []

        async def handler(event: dict) -> None:
            received.append(event)

        engine.on("test.event", handler)
        await engine.emit("test.event", {"data": "hello"})
        assert len(received) == 1
        assert received[0]["data"] == "hello"

    @pytest.mark.asyncio
    async def test_emit_ticket_event(self, engine: NotificationEngine) -> None:
        count = await engine.emit_ticket_event(
            event_type="ticket_created",
            ticket_data={"id": "abc123", "title": "Test"},
            sender="alice",
        )
        assert count >= 0

    @pytest.mark.asyncio
    async def test_emit_user_event(self, engine: NotificationEngine) -> None:
        count = await engine.emit_user_event("connected", "alice", {"status": "online"})
        assert count >= 0

    @pytest.mark.asyncio
    async def test_emit_system_event(self, engine: NotificationEngine) -> None:
        count = await engine.emit_system_event("startup", "Server started")
        assert count >= 0

    @pytest.mark.asyncio
    async def test_start_stop(self, engine: NotificationEngine) -> None:
        await engine.start()
        assert engine._running is True
        await engine.stop()
        assert engine._running is False

    def test_get_status(self, engine: NotificationEngine) -> None:
        status = engine.get_status()
        assert "running" in status
        assert "registered_handlers" in status
        assert "queue_size" in status

    @pytest.mark.asyncio
    async def test_queue_event(self, engine: NotificationEngine) -> None:
        await engine.queue_event("test", {"data": "queued"})
        assert engine._event_queue.qsize() == 1
