"""Ticket management CLI commands."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click

from taskflow.core.models import Ticket, TicketPriority, TicketStatus
from taskflow.storage.sqlite_store import SQLiteStore
from taskflow.utils.formatters import format_ticket_detail, format_ticket_table
from taskflow.utils.validators import (
    ValidationError,
    validate_assignee,
    validate_priority,
    validate_status,
    validate_ticket_title,
)


def _get_store(ctx: click.Context) -> SQLiteStore:
    """Get the SQLite store from the click context."""
    if ctx.obj is None:
        db_path = Path(click.get_app_dir("taskflow")) / "taskflow.db"
        ctx.obj = {"store": SQLiteStore(db_path), "user": "default"}
    return ctx.obj["store"]


def _get_user(ctx: click.Context) -> str:
    """Get the current user from the click context."""
    if ctx.obj is None:
        return "default"
    return ctx.obj.get("user", "default")


@click.group()
def tickets():
    """Manage tickets/issues."""
    pass


@tickets.command("create")
@click.option("--title", "-t", required=True, help="Ticket title")
@click.option("--description", "-d", default=None, help="Ticket description")
@click.option(
    "--priority",
    "-p",
    default="medium",
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    help="Ticket priority",
)
@click.option("--assignee", "-a", default=None, help="Assignee name")
@click.option("--label", "-l", multiple=True, help="Labels to attach")
@click.pass_context
def create_ticket(ctx, title, description, priority, assignee, label):
    """Create a new ticket."""
    try:
        validated_title = validate_ticket_title(title)
        priority_enum = validate_priority(priority)
    except ValidationError as e:
        click.echo(f"Error: {e}", err=True)
        return

    if assignee:
        try:
            assignee = validate_assignee(assignee)
        except ValidationError as e:
            click.echo(f"Error: {e}", err=True)
            return

    store = _get_store(ctx)
    user = _get_user(ctx)

    ticket = Ticket(
        title=validated_title,
        description=description,
        priority=priority_enum,
        assignee=assignee,
        labels=list(label),
        creator=user,
    )

    store.save_ticket(ticket)
    click.echo(f"Created ticket #{ticket.id[:8]}: {ticket.title}")


@tickets.command("list")
@click.option("--status", "-s", default=None, help="Filter by status")
@click.option("--priority", "-p", default=None, help="Filter by priority")
@click.option("--assignee", "-a", default=None, help="Filter by assignee")
@click.option("--label", "-l", multiple=True, help="Filter by labels")
@click.option("--search", "-q", default=None, help="Search in title/description")
@click.pass_context
def list_tickets(ctx, status, priority, assignee, label, search):
    """List all tickets with optional filters."""
    store = _get_store(ctx)

    filters = {}
    if status:
        try:
            filters["status"] = validate_status(status)
        except ValidationError as e:
            click.echo(f"Error: {e}", err=True)
            return
    if priority:
        try:
            filters["priority"] = validate_priority(priority)
        except ValidationError as e:
            click.echo(f"Error: {e}", err=True)
            return
    if assignee:
        filters["assignee"] = assignee
    if label:
        filters["labels"] = list(label)
    if search:
        filters["search"] = search

    tickets_list = store.list_tickets(**filters)

    if not tickets_list:
        click.echo("No tickets found.")
        return

    from rich.console import Console

    Console().print(format_ticket_table(tickets_list))


@tickets.command("show")
@click.argument("ticket_id")
@click.pass_context
def show_ticket(ctx, ticket_id):
    """Show details of a specific ticket."""
    store = _get_store(ctx)
    ticket = store.get_ticket(ticket_id)

    if ticket is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        return

    format_ticket_detail(ticket)


@tickets.command("update")
@click.argument("ticket_id")
@click.option("--title", "-t", default=None, help="New title")
@click.option("--description", "-d", default=None, help="New description")
@click.option("--status", "-s", default=None, help="New status")
@click.option("--priority", "-p", default=None, help="New priority")
@click.option("--assignee", "-a", default=None, help="New assignee")
@click.pass_context
def update_ticket(ctx, ticket_id, title, description, status, priority, assignee):
    """Update an existing ticket."""
    store = _get_store(ctx)
    ticket = store.get_ticket(ticket_id)

    if ticket is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        return

    if title:
        try:
            ticket.title = validate_ticket_title(title)
        except ValidationError as e:
            click.echo(f"Error: {e}", err=True)
            return

    if description is not None:
        ticket.description = description

    if status:
        try:
            ticket.status = validate_status(status)
        except ValidationError as e:
            click.echo(f"Error: {e}", err=True)
            return

    if priority:
        try:
            ticket.priority = validate_priority(priority)
        except ValidationError as e:
            click.echo(f"Error: {e}", err=True)
            return

    if assignee:
        try:
            ticket.assignee = validate_assignee(assignee)
        except ValidationError as e:
            click.echo(f"Error: {e}", err=True)
            return

    ticket.updated_at = datetime.now(timezone.utc)

    if ticket.status in (TicketStatus.DONE, TicketStatus.CLOSED):
        ticket.closed_at = datetime.now(timezone.utc)

    store.save_ticket(ticket)
    click.echo(f"Updated ticket #{ticket.id[:8]}")


@tickets.command("delete")
@click.argument("ticket_id")
@click.confirmation_option(prompt="Are you sure you want to delete this ticket?")
@click.pass_context
def delete_ticket(ctx, ticket_id):
    """Delete a ticket."""
    store = _get_store(ctx)
    deleted = store.delete_ticket(ticket_id)

    if deleted:
        click.echo(f"Deleted ticket #{ticket_id[:8]}")
    else:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)


@tickets.command("add-label")
@click.argument("ticket_id")
@click.argument("label_name")
@click.pass_context
def add_label(ctx, ticket_id, label_name):
    """Add a label to a ticket."""
    store = _get_store(ctx)
    ticket = store.get_ticket(ticket_id)

    if ticket is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        return

    if label_name not in ticket.labels:
        ticket.labels.append(label_name)
        ticket.updated_at = datetime.now(timezone.utc)
        store.save_ticket(ticket)
        click.echo(f"Added label '{label_name}' to ticket #{ticket.id[:8]}")
    else:
        click.echo(f"Label '{label_name}' already exists on ticket #{ticket.id[:8]}")


@tickets.command("remove-label")
@click.argument("ticket_id")
@click.argument("label_name")
@click.pass_context
def remove_label(ctx, ticket_id, label_name):
    """Remove a label from a ticket."""
    store = _get_store(ctx)
    ticket = store.get_ticket(ctx)

    if ticket is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        return

    if label_name in ticket.labels:
        ticket.labels.remove(label_name)
        ticket.updated_at = datetime.now(timezone.utc)
        store.save_ticket(ticket)
        click.echo(f"Removed label '{label_name}' from ticket #{ticket.id[:8]}")
    else:
        click.echo(f"Label '{label_name}' not found on ticket #{ticket.id[:8]}")
