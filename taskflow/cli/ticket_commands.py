"""Ticket management CLI commands."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Optional

import click

from taskflow.models.ticket import Priority, Status
from taskflow.services.ticket_service import TicketService
from taskflow.utils.formatter import format_ticket_table, format_ticket_json


@click.group(name="ticket")
def ticket() -> None:
    """Manage tickets/issues.

    Create, update, list, and search tickets with labels, priority, and assignee support.
    """
    pass


@ticket.command(name="create")
@click.option("--title", "-t", required=True, help="Ticket title")
@click.option("--description", "-d", default="", help="Ticket description")
@click.option(
    "--priority", "-p",
    default="medium",
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    help="Ticket priority",
)
@click.option("--assignee", "-a", default=None, help="Assignee username")
@click.option("--reporter", "-r", default=None, help="Reporter username")
@click.option("--label", "-l", multiple=True, help="Labels to add (can specify multiple)")
@click.option("--due-date", default=None, help="Due date (ISO format: YYYY-MM-DD)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def create_ticket(
    title: str,
    description: str,
    priority: str,
    assignee: Optional[str],
    reporter: Optional[str],
    label: tuple[str, ...],
    due_date: Optional[str],
    as_json: bool,
) -> None:
    """Create a new ticket."""
    service = TicketService()
    ticket = service.create_ticket(
        title=title,
        description=description,
        priority=priority,
        assignee=assignee,
        reporter=reporter,
        labels=list(label),
        due_date=due_date,
    )
    if as_json:
        click.echo(format_ticket_json(ticket))
    else:
        click.echo(f"Created ticket: {ticket.id}")
        click.echo(f"  Title: {ticket.title}")
        click.echo(f"  Priority: {ticket.priority.value}")
        click.echo(f"  Status: {ticket.status.value}")
        if ticket.assignee:
            click.echo(f"  Assignee: {ticket.assignee}")
        if label:
            click.echo(f"  Labels: {', '.join(ticket.labels)}")


@ticket.command(name="list")
@click.option("--status", "-s", default=None, help="Filter by status")
@click.option("--priority", "-p", default=None, help="Filter by priority")
@click.option("--assignee", "-a", default=None, help="Filter by assignee")
@click.option("--label", "-l", default=None, help="Filter by label")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_tickets(
    status: Optional[str],
    priority: Optional[str],
    assignee: Optional[str],
    label: Optional[str],
    as_json: bool,
) -> None:
    """List tickets with optional filters."""
    service = TicketService()
    tickets = service.list_tickets(
        status=status,
        priority=priority,
        assignee=assignee,
        label=label,
    )
    if not tickets:
        click.echo("No tickets found.")
        return
    if as_json:
        click.echo(format_ticket_json(tickets))
    else:
        click.echo(format_ticket_table(tickets))


@ticket.command(name="show")
@click.argument("ticket_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_ticket(ticket_id: str, as_json: bool) -> None:
    """Show ticket details."""
    service = TicketService()
    ticket = service.get_ticket(ticket_id)
    if ticket is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        sys.exit(1)
    if as_json:
        click.echo(format_ticket_json(ticket))
    else:
        click.echo(f"ID:         {ticket.id}")
        click.echo(f"Title:      {ticket.title}")
        click.echo(f"Status:     {ticket.status.value}")
        click.echo(f"Priority:   {ticket.priority.value}")
        click.echo(f"Assignee:   {ticket.assignee or 'Unassigned'}")
        click.echo(f"Reporter:   {ticket.reporter or 'N/A'}")
        click.echo(f"Labels:     {', '.join(ticket.labels) if ticket.labels else 'None'}")
        click.echo(f"Created:    {ticket.created_at.isoformat()}")
        click.echo(f"Updated:    {ticket.updated_at.isoformat()}")
        if ticket.due_date:
            click.echo(f"Due Date:   {ticket.due_date.isoformat()}")
            if ticket.is_overdue():
                click.echo("           ⚠ OVERDUE")
        if ticket.description:
            click.echo(f"Description: {ticket.description}")


@ticket.command(name="update")
@click.argument("ticket_id")
@click.option("--title", "-t", default=None, help="New title")
@click.option("--description", "-d", default=None, help="New description")
@click.option(
    "--priority", "-p",
    default=None,
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    help="New priority",
)
@click.option(
    "--status", "-s",
    default=None,
    type=click.Choice(["todo", "in_progress", "in_review", "done", "cancelled"], case_sensitive=False),
    help="New status",
)
@click.option("--assignee", "-a", default=None, help="New assignee")
def update_ticket(
    ticket_id: str,
    title: Optional[str],
    description: Optional[str],
    priority: Optional[str],
    status: Optional[str],
    assignee: Optional[str],
) -> None:
    """Update a ticket."""
    service = TicketService()
    updated = service.update_ticket(
        ticket_id=ticket_id,
        title=title,
        description=description,
        priority=priority,
        status=status,
        assignee=assignee,
    )
    if updated is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        sys.exit(1)
    click.echo(f"Updated ticket: {updated.id}")


@ticket.command(name="delete")
@click.argument("ticket_id")
@click.confirmation_option(prompt="Are you sure you want to delete this ticket?")
def delete_ticket(ticket_id: str) -> None:
    """Delete a ticket."""
    service = TicketService()
    if service.delete_ticket(ticket_id):
        click.echo(f"Deleted ticket: {ticket_id}")
    else:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        sys.exit(1)


@ticket.command(name="assign")
@click.argument("ticket_id")
@click.argument("assignee")
def assign_ticket(ticket_id: str, assignee: str) -> None:
    """Assign a ticket to a user."""
    service = TicketService()
    ticket = service.assign_ticket(ticket_id, assignee)
    if ticket is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        sys.exit(1)
    click.echo(f"Assigned ticket {ticket_id} to {assignee}")


@ticket.command(name="label")
@click.argument("ticket_id")
@click.argument("label_name")
@click.option("--remove", "-r", is_flag=True, help="Remove label instead of adding")
def manage_label(ticket_id: str, label_name: str, remove: bool) -> None:
    """Add or remove a label from a ticket."""
    service = TicketService()
    if remove:
        ticket = service.remove_label(ticket_id, label_name)
        action = "Removed"
    else:
        ticket = service.add_label(ticket_id, label_name)
        action = "Added"
    if ticket is None:
        click.echo(f"Ticket '{ticket_id}' not found.", err=True)
        sys.exit(1)
    click.echo(f"{action} label '{label_name}' on ticket {ticket_id}")


@ticket.command(name="search")
@click.argument("query")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_tickets(query: str, as_json: bool) -> None:
    """Search tickets by title or description."""
    service = TicketService()
    tickets = service.search_tickets(query)
    if not tickets:
        click.echo("No tickets found matching query.")
        return
    if as_json:
        click.echo(format_ticket_json(tickets))
    else:
        click.echo(format_ticket_table(tickets))


@ticket.command(name="stats")
def ticket_stats() -> None:
    """Show ticket statistics."""
    service = TicketService()
    stats = service.get_stats()
    click.echo("Ticket Statistics:")
    click.echo(f"  Total: {stats['total']}")
    click.echo("  By Status:")
    for status in Status:
        count = stats.get(status.value, 0)
        click.echo(f"    {status.value}: {count}")
    click.echo("  By Priority:")
    for priority in Priority:
        count = stats.get(f"priority_{priority.value}", 0)
        click.echo(f"    {priority.value}: {count}")
    click.echo(f"  Unassigned: {stats['unassigned']}")
    click.echo(f"  Overdue: {stats['overdue']}")
