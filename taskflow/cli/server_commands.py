"""Server CLI commands for real-time collaboration."""

from __future__ import annotations

import click

from taskflow.server.app import create_app
from taskflow.server.config import ServerConfig


@click.group(name="server")
def server() -> None:
    """Server commands for real-time collaboration.

    Start the WebSocket server for live updates and notifications.
    """
    pass


@server.command(name="start")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=8765, type=int, help="Port to listen on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--log-level", default="info", help="Logging level")
def start_server(host: str, port: int, reload: bool, log_level: str) -> None:
    """Start the TaskFlow WebSocket server."""
    import uvicorn

    config = ServerConfig(host=host, port=port)
    app = create_app(config)

    click.echo(f"Starting TaskFlow server on {host}:{port}")
    click.echo(f"WebSocket endpoint: ws://{host}:{port}/ws")
    click.echo(f"API endpoint: http://{host}:{port}/api")
    click.echo("Press Ctrl+C to stop")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


@server.command(name="status")
@click.option("--host", "-h", default="127.0.0.1", help="Server host")
@click.option("--port", "-p", default=8765, type=int, help="Server port")
def server_status(host: str, port: int) -> None:
    """Check server status."""
    import urllib.request
    import urllib.error

    url = f"http://{host}:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = response.read().decode()
            click.echo(f"Server is running on {host}:{port}")
            click.echo(f"Response: {data}")
    except urllib.error.URLError:
        click.echo(f"Server is not running on {host}:{port}", err=True)
