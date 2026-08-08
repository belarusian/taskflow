"""Output formatting utilities for CLI."""

from __future__ import annotations

import json
from typing import Any

from taskflow.models.ticket import Ticket


def format_ticket_table(tickets: list[Ticket]) -> str:
    """Format tickets as a table string."""
    if not tickets:
        return "No tickets found."

    headers = ["ID", "Title", "Status", "Priority", "Assignee", "Labels"]
    rows = []
    for t in tickets:
        rows.append([
            t.id[:8],
            t.title[:30],
            t.status.value,
            t.priority.value,
            t.assignee or "-",
            ", ".join(t.labels[:3]) if t.labels else "-",
        ])

    col_widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    col_widths = [max(w, len(h)) for w, h in zip(col_widths, headers)]

    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "  ".join("-" * w for w in col_widths)

    lines = [header_line, separator]
    for row in rows:
        line = "  ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        lines.append(line)

    return "\n".join(lines)


def format_ticket_json(data: Any) -> str:
    """Format ticket data as JSON string."""
    if isinstance(data, Ticket):
        return json.dumps(data.model_dump(), indent=2, default=str)
    if isinstance(data, list):
        return json.dumps(
            [d.model_dump() if isinstance(d, Ticket) else d for d in data],
            indent=2,
            default=str,
        )
    return json.dumps(data, indent=2, default=str)


def format_priority(priority: str) -> str:
    """Format priority with visual indicator."""
    indicators = {
        "critical": "🔴 CRITICAL",
        "high": "🟠 HIGH",
        "medium": "🟡 MEDIUM",
        "low": "🟢 LOW",
    }
    return indicators.get(priority.lower(), priority.upper())


def format_status(status: str) -> str:
    """Format status with visual indicator."""
    indicators = {
        "todo": "⬜ TODO",
        "in_progress": "🔵 IN_PROGRESS",
        "in_review": "🟣 IN_REVIEW",
        "done": "✅ DONE",
        "cancelled": "❌ CANCELLED",
    }
    return indicators.get(status.lower(), status.upper())
