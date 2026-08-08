"""Formatting utilities for TaskFlow CLI output."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table

from taskflow.core.models import Ticket

console = Console()


def format_timestamp(dt: Optional[datetime]) -> str:
    """Format a datetime object for display.

    Args:
        dt: The datetime to format.

    Returns:
        Formatted timestamp string, or 'N/A' if None.
    """
    if dt is None:
        return "N/A"
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    if diff.days > 0:
        return dt.strftime("%Y-%m-%d %H:%M")
    elif diff.seconds < 60:
        return f"{diff.seconds}s ago"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60}m ago"
    else:
        return f"{diff.seconds // 3600}h ago"


def format_priority(priority: str) -> str:
    """Format priority with visual indicator.

    Args:
        priority: The priority string.

    Returns:
        Formatted priority string with emoji.
    """
    priority_map = {
        "critical": "[red]🔴 Critical[/red]",
        "high": "[orange1]🟠 High[/orange1]",
        "medium": "[yellow]🟡 Medium[/yellow]",
        "low": "[green]🟢 Low[/green]",
    }
    return priority_map.get(priority, priority)


def format_status(status: str) -> str:
    """Format status with visual indicator.

    Args:
        status: The status string.

    Returns:
        Formatted status string with emoji.
    """
    status_map = {
        "open": "[blue]📋 Open[/blue]",
        "in_progress": "[cyan]🔄 In Progress[/cyan]",
        "in_review": "[magenta]👀 In Review[/magenta]",
        "done": "[green]✅ Done[/green]",
        "closed": "[dim]❌ Closed[/dim]",
    }
    return status_map.get(status, status)


def format_ticket_table(tickets: list[Ticket]) -> Table:
    """Create a Rich table for displaying tickets.

    Args:
        tickets: List of tickets to display.

    Returns:
        A Rich Table object.
    """
    table = Table(title="Tickets", show_header=True, header_style="bold magenta")

    table.add_column("ID", style="dim", width=16)
    table.add_column("Title", style="cyan", no_wrap=False)
    table.add_column("Status", style="green", width=15)
    table.add_column("Priority", width=15)
    table.add_column("Assignee", style="yellow", width=12)
    table.add_column("Labels", width=20)
    table.add_column("Created", style="dim", width=12)

    for ticket in tickets:
        labels_str = ", ".join(ticket.labels) if ticket.labels else "-"
        table.add_row(
            ticket.id[:8],
            ticket.title,
            format_status(ticket.status.value),
            format_priority(ticket.priority.value),
            ticket.assignee or "-",
            labels_str,
            format_timestamp(ticket.created_at),
        )

    return table


def format_ticket_detail(ticket: Ticket) -> None:
    """Print detailed ticket information.

    Args:
        ticket: The ticket to display.
    """
    console.print(f"\n[bold]Ticket #{ticket.id[:8]}[/bold]")
    console.print(f"  [bold]Title:[/bold] {ticket.title}")
    if ticket.description:
        console.print(f"  [bold]Description:[/bold] {ticket.description}")
    console.print(f"  [bold]Status:[/bold] {format_status(ticket.status.value)}")
    console.print(f"  [bold]Priority:[/bold] {format_priority(ticket.priority.value)}")
    console.print(f"  [bold]Assignee:[/bold] {ticket.assignee or 'Unassigned'}")
    if ticket.labels:
        console.print(f"  [bold]Labels:[/bold] {', '.join(ticket.labels)}")
    console.print(f"  [bold]Created:[/bold] {format_timestamp(ticket.created_at)}")
    console.print(f"  [bold]Updated:[/bold] {format_timestamp(ticket.updated_at)}")
    if ticket.closed_at:
        console.print(f"  [bold]Closed:[/bold] {format_timestamp(ticket.closed_at)}")
    if ticket.creator:
        console.print(f"  [bold]Creator:[/bold] {ticket.creator}")
    console.print()
