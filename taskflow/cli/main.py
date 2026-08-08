"""Main CLI entry point for TaskFlow."""

from __future__ import annotations

import click

from taskflow import __version__
from taskflow.cli.tickets import tickets
from taskflow.cli.labels import labels
from taskflow.cli.project import project
from taskflow.cli.ws import ws


@click.group()
@click.version_option(version=__version__, prog_name="taskflow")
def cli():
    """TaskFlow - Ticket tracking with real-time collaboration."""
    pass


# Register subcommands
cli.add_command(tickets, "tickets")
cli.add_command(tickets, "ticket")
cli.add_command(labels, "labels")
cli.add_command(labels, "label")
cli.add_command(project, "project")
cli.add_command(project, "init")
cli.add_command(ws, "ws")
cli.add_command(ws, "websocket")


if __name__ == "__main__":
    cli()
