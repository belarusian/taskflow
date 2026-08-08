"""Main CLI entry point for TaskFlow."""

from __future__ import annotations

import click

from taskflow import __version__
from taskflow.cli.ticket_commands import ticket
from taskflow.cli.user_commands import user
from taskflow.cli.label_commands import label
from taskflow.cli.notification_commands import notification
from taskflow.cli.server_commands import server


@click.group()
@click.version_option(version=__version__, prog_name="taskflow")
def main() -> None:
    """TaskFlow - A CLI tool for ticket tracking with real-time collaboration.

    Manage tickets, users, labels, and collaborate in real-time.
    """
    pass


# Register subcommands
main.add_command(ticket)
main.add_command(user)
main.add_command(label)
main.add_command(notification)
main.add_command(server)


if __name__ == "__main__":
    main()
