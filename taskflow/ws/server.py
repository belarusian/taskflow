"""WebSocket server for real-time collaboration."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import websockets
from websockets.server import WebSocketServerProtocol

from taskflow.ws.handlers import MessageHandler, WebSocketMessage, MessageType

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for TaskFlow real-time collaboration."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        handler: Optional[MessageHandler] = None,
    ):
        """Initialize the WebSocket server.

        Args:
            host: Host to bind to.
            port: Port to listen on.
            handler: Optional message handler instance.
        """
        self.host = host
        self.port = port
        self.handler = handler or MessageHandler()
        self._clients: dict[str, WebSocketServerProtocol] = {}
        self._client_ids: dict[WebSocketServerProtocol, str] = {}
        self._server = None
        self._running = False

    @property
    def client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self._clients)

    async def _register_client(
        self, websocket: WebSocketServerProtocol
    ) -> str:
        """Register a new client connection.

        Args:
            websocket: The WebSocket connection.

        Returns:
            The assigned client ID.
        """
        import uuid

        client_id = str(uuid.uuid4())[:8]
        self._clients[client_id] = websocket
        self._client_ids[websocket] = client_id

        # Notify about user joining
        join_msg = WebSocketMessage(
            type=MessageType.USER_JOINED,
            payload={"client_id": client_id},
            sender=client_id,
        )
        await self._broadcast(join_msg, exclude=client_id)

        logger.info(f"Client {client_id} connected. Total: {self.client_count}")
        return client_id

    async def _unregister_client(
        self, websocket: WebSocketServerProtocol
    ) -> Optional[str]:
        """Unregister a client connection.

        Args:
            websocket: The WebSocket connection.

        Returns:
            The client ID if found, None otherwise.
        """
        client_id = self._client_ids.pop(websocket, None)
        if client_id:
            self._clients.pop(client_id, None)

            # Notify about user leaving
            leave_msg = WebSocketMessage(
                type=MessageType.USER_LEFT,
                payload={"client_id": client_id},
                sender=client_id,
            )
            await self._broadcast(leave_msg)

            logger.info(f"Client {client_id} disconnected. Total: {self.client_count}")
        return client_id

    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a single client connection.

        Args:
            websocket: The WebSocket connection.
        """
        client_id = await self._register_client(websocket)

        # Send welcome message
        welcome = WebSocketMessage(
            type=MessageType.PONG,
            payload={
                "message": "Connected to TaskFlow",
                "client_id": client_id,
            },
            sender="server",
        )
        await websocket.send(welcome.to_json())

        try:
            async for message in websocket:
                try:
                    ws_message = WebSocketMessage.from_json(message)
                    response = await self.handler.handle(ws_message, client_id)

                    if response:
                        await websocket.send(response.to_json())

                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    error_msg = WebSocketMessage(
                        type=MessageType.ERROR,
                        payload={"error": str(e)},
                        sender="server",
                    )
                    await websocket.send(error_msg.to_json())
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for {client_id}")
        finally:
            await self._unregister_client(websocket)

    async def _broadcast(
        self,
        message: WebSocketMessage,
        exclude: Optional[str] = None,
    ) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast.
            exclude: Optional client ID to exclude from broadcast.
        """
        msg_json = message.to_json()
        tasks = []
        for client_id, websocket in self._clients.items():
            if client_id != exclude:
                tasks.append(self._safe_send(websocket, msg_json))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_send(
        self, websocket: WebSocketServerProtocol, message: str
    ) -> None:
        """Safely send a message to a client.

        Args:
            websocket: The WebSocket connection.
            message: The message to send.
        """
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            client_id = self._client_ids.get(websocket)
            if client_id:
                await self._unregister_client(websocket)

    async def broadcast_event(
        self,
        event_type: str,
        payload: dict,
        sender: Optional[str] = None,
    ) -> None:
        """Broadcast an event to all subscribers.

        Args:
            event_type: The event type.
            payload: The event payload.
            sender: Optional sender identifier.
        """
        message = WebSocketMessage(
            type=event_type,
            payload=payload,
            sender=sender,
        )
        subscribers = self.handler.get_subscribers(event_type)
        if subscribers:
            msg_json = message.to_json()
            tasks = []
            for client_id in subscribers:
                ws = self._clients.get(client_id)
                if ws:
                    tasks.append(self._safe_send(ws, msg_json))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            await self._broadcast(message, exclude=sender)

    async def start(self) -> None:
        """Start the WebSocket server."""
        self._running = True
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")

        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=20,
        )

        logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")

        try:
            await self._server.wait_closed()
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("WebSocket server stopped")
