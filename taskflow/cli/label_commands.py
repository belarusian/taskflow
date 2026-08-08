"""Label management CLI commands."""

from __future__ import annotations

import sys

import click

from taskflow.services.label_service import LabelService


@click.group(name="label")
def label() -> None:
    """Manage labels.

    Create, update, list, and delete labels for ticket categorization.
    """
    pass


@label.command(name="create")
@click.option("--name", "-n", required=True, help="Label name")
@click.option("--color", "-c", default="#666666", help="Hex color code")
@click.option("--description", "-d", default="", help="Label description")
def create_label(name: str, color: str, description: str) -> None:
    """Create a new label."""
    service = LabelService()
    try:
        label = service.create_label(
            name=name,
            color=color,
            description=description,
        )
        click.echo(f"Created label: {label.name}")
        click.echo(f"  Color: {label.color}")
        if label.description:
            click.echo(f"  Description: {label.description}")
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@label.command(name="list")
def list_labels() -> None:
    """List all labels."""
    service = LabelService()
    labels = service.list_labels()
    if not labels:
        click.echo("No labels found.")
        return
    click.echo(f"{'Name':<20} {'Color':<10} {'Description':<40}")
    click.echo("-" * 70)
    for l in labels:
        click.echo(f"{l.name:<20} {l.color:<10} {l.description:<40}")


@label.command(name="delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this label?")
def delete_label(name: str) -> None:
    """Delete a label."""
    service = LabelService()
    if service.delete_label(name):
        click.echo(f"Deleted label: {name}")
    else:
        click.echo(f"Label '{name}' not found.", err=True)
        sys.exit(1)
