"""Notification CLI commands."""

from __future__ import annotations

import sys

import click

from taskflow.services.notification_service import NotificationService


@click.group(name="notification")
def notification() -> None:
    """Manage notifications.

    View and manage real-time collaboration notifications.
    """
    pass


@notification.command(name="list")
@click.option("--user", "-u", required=True, help="Username to get notifications for")
@click.option("--unread-only", is_flag=True, help="Show only unread notifications")
def list_notifications(user: str, unread_only: bool) -> None:
    """List notifications for a user."""
    service = NotificationService()
    if unread_only:
        notifications = service.get_unread_notifications(user)
    else:
        notifications = service.get_user_notifications(user)
    if not notifications:
        click.echo("No notifications found.")
        return
    click.echo(f"Notifications for {user}:")
    click.echo("-" * 70)
    for n in notifications:
        read_status = "✓" if n.is_read else "◌"
        click.echo(f"[{read_status}] {n.title}")
        click.echo(f"    {n.message}")
        click.echo(f"    Type: {n.type.value} | Created: {n.created_at.isoformat()}")
        click.echo()


@notification.command(name="unread-count")
@click.option("--user", "-u", required=True, help="Username")
def unread_count(user: str) -> None:
    """Show unread notification count for a user."""
    service = NotificationService()
    count = service.get_unread_count(user)
    click.echo(f"Unread notifications for {user}: {count}")


@notification.command(name="mark-read")
@click.argument("notification_id")
def mark_read(notification_id: str) -> None:
    """Mark a notification as read."""
    service = NotificationService()
    if service.mark_as_read(notification_id):
        click.echo(f"Marked notification {notification_id} as read")
    else:
        click.echo(f"Notification '{notification_id}' not found.", err=True)
        sys.exit(1)


@notification.command(name="mark-all-read")
@click.option("--user", "-u", required=True, help="Username")
def mark_all_read(user: str) -> None:
    """Mark all notifications as read for a user."""
    service = NotificationService()
    count = service.mark_all_read(user)
    click.echo(f"Marked {count} notifications as read for {user}")
