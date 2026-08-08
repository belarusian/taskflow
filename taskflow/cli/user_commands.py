"""User management CLI commands."""

from __future__ import annotations

import sys
from typing import Optional

import click

from taskflow.services.user_service import UserService


@click.group(name="user")
def user() -> None:
    """Manage users.

    Create, update, list, and manage user accounts.
    """
    pass


@user.command(name="create")
@click.option("--username", "-u", required=True, help="Username")
@click.option("--email", "-e", default="", help="Email address")
@click.option("--display-name", "-n", default="", help="Display name")
def create_user(username: str, email: str, display_name: str) -> None:
    """Create a new user."""
    service = UserService()
    try:
        user = service.create_user(
            username=username,
            email=email,
            display_name=display_name,
        )
        click.echo(f"Created user: {user.username}")
        click.echo(f"  Display Name: {user.display_name}")
        if user.email:
            click.echo(f"  Email: {user.email}")
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@user.command(name="list")
@click.option("--active-only", is_flag=True, help="Show only active users")
def list_users(active_only: bool) -> None:
    """List all users."""
    service = UserService()
    users = service.list_users(active_only=active_only)
    if not users:
        click.echo("No users found.")
        return
    click.echo(f"{'Username':<20} {'Display Name':<25} {'Email':<30} {'Status':<10}")
    click.echo("-" * 85)
    for u in users:
        status = "active" if u.is_active else "inactive"
        online = " (online)" if u.connected_clients > 0 else ""
        click.echo(
            f"{u.username:<20} {u.display_name:<25} {u.email:<30} {status}{online:<10}"
        )


@user.command(name="show")
@click.argument("username")
def show_user(username: str) -> None:
    """Show user details."""
    service = UserService()
    user = service.get_user(username)
    if user is None:
        click.echo(f"User '{username}' not found.", err=True)
        sys.exit(1)
    click.echo(f"Username:     {user.username}")
    click.echo(f"Display Name: {user.display_name}")
    click.echo(f"Email:        {user.email or 'N/A'}")
    click.echo(f"Active:       {user.is_active}")
    click.echo(f"Connected:    {user.connected_clients} clients")
    click.echo(f"Last Seen:    {user.last_seen.isoformat() if user.last_seen else 'Never'}")


@user.command(name="delete")
@click.argument("username")
@click.confirmation_option(prompt="Are you sure you want to delete this user?")
def delete_user(username: str) -> None:
    """Delete a user."""
    service = UserService()
    if service.delete_user(username):
        click.echo(f"Deleted user: {username}")
    else:
        click.echo(f"User '{username}' not found.", err=True)
        sys.exit(1)
