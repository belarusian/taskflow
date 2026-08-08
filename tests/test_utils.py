"""Tests for TaskFlow utility modules."""

from __future__ import annotations

from taskflow.models.ticket import Priority, Status, Ticket
from taskflow.utils.formatter import (
    format_ticket_table,
    format_ticket_json,
    format_priority,
    format_status,
)
from taskflow.utils.config import get_config_path, _deep_merge


class TestFormatter:
    """Tests for output formatter utilities."""

    def test_format_ticket_table_empty(self) -> None:
        result = format_ticket_table([])
        assert "No tickets found" in result

    def test_format_ticket_table_single(self) -> None:
        tickets = [Ticket(title="Test", priority=Priority.HIGH)]
        result = format_ticket_table(tickets)
        assert "Test" in result
        assert "high" in result

    def test_format_ticket_table_multiple(self) -> None:
        tickets = [
            Ticket(title="First", priority=Priority.HIGH, assignee="alice"),
            Ticket(title="Second", priority=Priority.LOW),
        ]
        result = format_ticket_table(tickets)
        assert "First" in result
        assert "Second" in result
        assert "alice" in result

    def test_format_ticket_table_with_labels(self) -> None:
        tickets = [Ticket(title="Test", labels=["bug", "frontend"])]
        result = format_ticket_table(tickets)
        assert "bug" in result

    def test_format_ticket_json_single(self) -> None:
        ticket = Ticket(title="Test", priority=Priority.HIGH)
        result = format_ticket_json(ticket)
        assert "Test" in result
        assert "high" in result

    def test_format_ticket_json_list(self) -> None:
        tickets = [
            Ticket(title="A", priority=Priority.HIGH),
            Ticket(title="B", priority=Priority.LOW),
        ]
        result = format_ticket_json(tickets)
        assert "A" in result
        assert "B" in result

    def test_format_priority_critical(self) -> None:
        result = format_priority("critical")
        assert "CRITICAL" in result

    def test_format_priority_high(self) -> None:
        result = format_priority("high")
        assert "HIGH" in result

    def test_format_priority_medium(self) -> None:
        result = format_priority("medium")
        assert "MEDIUM" in result

    def test_format_priority_low(self) -> None:
        result = format_priority("low")
        assert "LOW" in result

    def test_format_status_todo(self) -> None:
        result = format_status("todo")
        assert "TODO" in result

    def test_format_status_done(self) -> None:
        result = format_status("done")
        assert "DONE" in result

    def test_format_status_in_progress(self) -> None:
        result = format_status("in_progress")
        assert "IN_PROGRESS" in result


class TestConfig:
    """Tests for configuration utilities."""

    def test_get_config_path(self) -> None:
        path = get_config_path()
        assert path.name == "config.yaml"
        assert ".taskflow" in str(path)

    def test_deep_merge_simple(self) -> None:
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self) -> None:
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 4, "z": 5}}
        result = _deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 4, "z": 5}, "b": 3}

    def test_deep_merge_empty_override(self) -> None:
        base = {"a": 1}
        result = _deep_merge(base, {})
        assert result == {"a": 1}

    def test_deep_merge_empty_base(self) -> None:
        result = _deep_merge({}, {"a": 1})
        assert result == {"a": 1}
