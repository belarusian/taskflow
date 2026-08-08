"""SQLite-based persistent storage for TaskFlow."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from taskflow.core.models import Ticket, TicketPriority, TicketStatus


class SQLiteStore:
    """SQLite-backed storage for tickets and labels."""

    def __init__(self, db_path: str | Path):
        """Initialize the SQLite store.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self) -> None:
        """Create parent directories for the database if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'open',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    assignee TEXT,
                    labels TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    creator TEXT
                );

                CREATE TABLE IF NOT EXISTS labels (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT NOT NULL DEFAULT '#000000',
                    description TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
                CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
                CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee);
                CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets(created_at);
                """
            )
            conn.commit()
        finally:
            conn.close()

    def save_ticket(self, ticket: Ticket) -> Ticket:
        """Save or update a ticket in the database.

        Args:
            ticket: The ticket to save.

        Returns:
            The saved ticket.
        """
        data = ticket.to_dict()
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO tickets (id, title, description, status, priority,
                    assignee, labels, created_at, updated_at, closed_at, creator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    description=excluded.description,
                    status=excluded.status,
                    priority=excluded.priority,
                    assignee=excluded.assignee,
                    labels=excluded.labels,
                    updated_at=excluded.updated_at,
                    closed_at=excluded.closed_at,
                    creator=excluded.creator
                """,
                (
                    data["id"],
                    data["title"],
                    data["description"],
                    data["status"],
                    data["priority"],
                    data["assignee"],
                    json.dumps(data["labels"]),
                    data["created_at"],
                    data["updated_at"],
                    data["closed_at"],
                    data["creator"],
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Retrieve a ticket by its ID.

        Args:
            ticket_id: The ticket ID to look up.

        Returns:
            The ticket if found, None otherwise.
        """
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_ticket(row)
        finally:
            conn.close()

    def list_tickets(
        self,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
        search: Optional[str] = None,
    ) -> list[Ticket]:
        """List tickets with optional filters.

        Args:
            status: Filter by ticket status.
            priority: Filter by ticket priority.
            assignee: Filter by assignee name.
            labels: Filter by label names (tickets must have all labels).
            search: Search in title and description.

        Returns:
            List of matching tickets.
        """
        query = "SELECT * FROM tickets WHERE 1=1"
        params: list = []

        if status:
            query += " AND status = ?"
            params.append(status.value)
        if priority:
            query += " AND priority = ?"
            params.append(priority.value)
        if assignee:
            query += " AND assignee = ?"
            params.append(assignee)
        if search:
            query += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY created_at DESC"

        conn = self._get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
            tickets = [self._row_to_ticket(row) for row in rows]

            if labels:
                tickets = [
                    t for t in tickets
                    if all(lbl in t.labels for lbl in labels)
                ]
            return tickets
        finally:
            conn.close()

    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket by its ID.

        Args:
            ticket_id: The ticket ID to delete.

        Returns:
            True if the ticket was deleted, False if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM tickets WHERE id = ?", (ticket_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def save_label(self, label_data: dict) -> dict:
        """Save or update a label.

        Args:
            label_data: Dictionary with label data.

        Returns:
            The saved label data.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO labels (id, name, color, description)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    color=excluded.color,
                    description=excluded.description
                """,
                (
                    label_data.get("id", ""),
                    label_data["name"],
                    label_data.get("color", "#000000"),
                    label_data.get("description"),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return label_data

    def list_labels(self) -> list[dict]:
        """List all labels.

        Returns:
            List of label dictionaries.
        """
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM labels").fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def count_tickets(self) -> int:
        """Count total number of tickets.

        Returns:
            Total ticket count.
        """
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM tickets").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_ticket(row: sqlite3.Row) -> Ticket:
        """Convert a database row to a Ticket object."""
        data = dict(row)
        data["labels"] = json.loads(data.get("labels", "[]"))
        return Ticket.from_dict(data)
