"""Server configuration for TaskFlow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServerConfig:
    """Configuration for the TaskFlow server."""

    host: str = "127.0.0.1"
    port: int = 8765
    ws_path: str = "/ws"
    api_prefix: str = "/api"
    max_connections: int = 100
    heartbeat_interval: int = 30
    message_buffer_size: int = 1000
    cors_origins: list[str] = field(
        default_factory=lambda: ["*"]
    )
    debug: bool = False

    def get_ws_url(self) -> str:
        """Get the WebSocket URL."""
        return f"ws://{self.host}:{self.port}{self.ws_path}"

    def get_api_url(self) -> str:
        """Get the API base URL."""
        return f"http://{self.host}:{self.port}{self.api_prefix}"

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "ws_path": self.ws_path,
            "api_prefix": self.api_prefix,
            "max_connections": self.max_connections,
            "heartbeat_interval": self.heartbeat_interval,
            "message_buffer_size": self.message_buffer_size,
            "debug": self.debug,
        }
