"""Label management CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from taskflow.storage.sqlite_store import SQLiteStore
from taskflow.utils.validators import ValidationError, validate_color, validate_label_name


def _get_store(ctx: click.Context) -> SQLiteStore:
    """Get the SQLite store from the click context."""
    if ctx.obj is None:
        db_path = Path(click.get_app_dir("taskflow")) / "taskflow.db"
        ctx.obj = {"store": SQLiteStore(db_path), "user": "default"}
    return ctx.obj["store"]


@click.group()
def labels():
    """Manage labels."""
    pass


@labels.command("create")
@click.option("--name", "-n", required=True, help="Label name")
@click.option("--color", "-c", default="#000000", help="Hex color code")
@click.option("--description", "-d", default=None, help="Label description")
@click.pass_context
def create_label(ctx, name, color, description):
    """Create a new label."""
    try:
        validated_name = validate_label_name(name)
        validated_color = validate_color(color)
    except ValidationError as e:
        click.echo(f"Error: {e}", err=True)
        return

    store = _get_store(ctx)
    label_data = {
        "name": validated_name,
        "color": validated_color,
        "description": description,
    }
    store.save_label(label_data)
    click.echo(f"Created label '{validated_name}' ({validated_color})")


@labels.command("list")
@click.pass_context
def list_labels(ctx):
    """List all labels."""
    store = _get_store(ctx)
    label_list = store.list_labels()

    if not label_list:
        click.echo("No labels found.")
        return

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Labels", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Color", width=10)
    table.add_column("Description", style="dim")

    for label in label_list:
        table.add_row(
            label["name"],
            label["color"],
            label.get("description") or "-",
        )

    Console().print(table)


@labels.command("delete")
@click.argument("label_name")
@click.pass_context
def delete_label(ctx, label_name):
    """Delete a label by name."""
    store = _get_store(ctx)
    conn = store._get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM labels WHERE name = ?", (label_name,)
        )
        conn.commit()
        if cursor.rowcount > 0:
            click.echo(f"Deleted label '{label_name}'")
        else:
            click.echo(f"Label '{label_name}' not found.", err=True)
    finally:
        conn.close()
