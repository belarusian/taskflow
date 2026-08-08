"""Project management CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from taskflow.storage.sqlite_store import SQLiteStore


@click.group()
def project():
    """Manage TaskFlow projects."""
    pass


@project.command("init")
@click.option("--path", "-p", default=".", help="Project directory")
@click.option("--name", "-n", default=None, help="Project name")
def init_project(path, name):
    """Initialize a new TaskFlow project."""
    project_dir = Path(path).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    config_file = project_dir / ".taskflow"
    if config_file.exists():
        click.echo(f"Project already initialized at {project_dir}")
        return

    project_name = name or project_dir.name

    config_data = {
        "name": project_name,
        "version": "0.1.0",
        "db_path": str(project_dir / ".taskflow" / "data.db"),
    }

    config_dir = project_dir / ".taskflow"
    config_dir.mkdir(exist_ok=True)

    import json

    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)

    # Initialize the database
    db_path = Path(config_data["db_path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLiteStore(db_path)

    click.echo(f"Initialized TaskFlow project '{project_name}' at {project_dir}")
    click.echo(f"Database: {db_path}")


@project.command("info")
@click.option("--path", "-p", default=".", help="Project directory")
def project_info(path):
    """Show project information."""
    project_dir = Path(path).resolve()
    config_file = project_dir / ".taskflow"

    if not config_file.exists():
        click.echo("No TaskFlow project found. Run 'taskflow project init' first.", err=True)
        return

    import json

    with open(config_file) as f:
        config = json.load(f)

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    panel = Panel(
        f"[bold]Name:[/bold] {config['name']}\n"
        f"[bold]Version:[/bold] {config['version']}\n"
        f"[bold]Database:[/bold] {config['db_path']}",
        title="TaskFlow Project",
        border_style="blue",
    )
    console.print(panel)

    # Show ticket stats
    db_path = Path(config["db_path"])
    if db_path.exists():
        store = SQLiteStore(db_path)
        count = store.count_tickets()
        console.print(f"\nTotal tickets: {count}")
