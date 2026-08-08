"""Tests for TaskFlow CLI commands."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from taskflow.cli.main import main
from taskflow.cli.ticket_commands import ticket
from taskflow.cli.user_commands import user
from taskflow.cli.label_commands import label
from taskflow.cli.notification_commands import notification


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestMainCLI:
    """Tests for main CLI entry point."""

    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "taskflow" in result.output.lower()
        assert "0.1.0" in result.output

    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ticket" in result.output.lower()
        assert "user" in result.output.lower()
        assert "label" in result.output.lower()


class TestTicketCLI:
    """Tests for ticket CLI commands."""

    def test_ticket_help(self, runner: CliRunner) -> None:
        result = runner.invoke(ticket, ["--help"])
        assert result.exit_code == 0
        assert "create" in result.output.lower()
        assert "list" in result.output.lower()

    @patch("taskflow.cli.ticket_commands.TicketService")
    def test_create_ticket(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.id = "abc123"
        mock_ticket.title = "Test Ticket"
        mock_ticket.priority = MagicMock(value="high")
        mock_ticket.status = MagicMock(value="todo")
        mock_ticket.assignee = "alice"
        mock_ticket.labels = ["bug"]
        mock_service.create_ticket.return_value = mock_ticket
        mock_service_cls.return_value = mock_service

        result = runner.invoke(ticket, [
            "create", "-t", "Test Ticket", "-p", "high",
            "-a", "alice", "-l", "bug",
        ])
        assert result.exit_code == 0
        assert "abc123" in result.output

    @patch("taskflow.cli.ticket_commands.TicketService")
    def test_list_tickets(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.list_tickets.return_value = []
        mock_service_cls.return_value = mock_service

        result = runner.invoke(ticket, ["list"])
        assert result.exit_code == 0
        assert "No tickets found" in result.output

    @patch("taskflow.cli.ticket_commands.TicketService")
    def test_show_ticket_not_found(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.get_ticket.return_value = None
        mock_service_cls.return_value = mock_service

        result = runner.invoke(ticket, ["show", "nonexistent"])
        assert result.exit_code == 1

    @patch("taskflow.cli.ticket_commands.TicketService")
    def test_search_tickets(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.search_tickets.return_value = []
        mock_service_cls.return_value = mock_service

        result = runner.invoke(ticket, ["search", "bug"])
        assert result.exit_code == 0


class TestUserCLI:
    """Tests for user CLI commands."""

    def test_user_help(self, runner: CliRunner) -> None:
        result = runner.invoke(user, ["--help"])
        assert result.exit_code == 0
        assert "create" in result.output.lower()

    @patch("taskflow.cli.user_commands.UserService")
    def test_create_user(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "alice"
        mock_user.display_name = "Alice"
        mock_user.email = "alice@example.com"
        mock_service.create_user.return_value = mock_user
        mock_service_cls.return_value = mock_service

        result = runner.invoke(user, ["create", "-u", "alice", "-e", "alice@example.com"])
        assert result.exit_code == 0
        assert "alice" in result.output

    @patch("taskflow.cli.user_commands.UserService")
    def test_create_duplicate_user(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.create_user.side_effect = ValueError("already exists")
        mock_service_cls.return_value = mock_service

        result = runner.invoke(user, ["create", "-u", "alice"])
        assert result.exit_code == 1

    @patch("taskflow.cli.user_commands.UserService")
    def test_list_users(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.list_users.return_value = []
        mock_service_cls.return_value = mock_service

        result = runner.invoke(user, ["list"])
        assert result.exit_code == 0


class TestLabelCLI:
    """Tests for label CLI commands."""

    def test_label_help(self, runner: CliRunner) -> None:
        result = runner.invoke(label, ["--help"])
        assert result.exit_code == 0
        assert "create" in result.output.lower()

    @patch("taskflow.cli.label_commands.LabelService")
    def test_create_label(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_label = MagicMock()
        mock_label.name = "bug"
        mock_label.color = "#FF0000"
        mock_label.description = ""
        mock_service.create_label.return_value = mock_label
        mock_service_cls.return_value = mock_service

        result = runner.invoke(label, ["create", "-n", "bug", "-c", "#FF0000"])
        assert result.exit_code == 0
        assert "bug" in result.output

    @patch("taskflow.cli.label_commands.LabelService")
    def test_list_labels(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.list_labels.return_value = []
        mock_service_cls.return_value = mock_service

        result = runner.invoke(label, ["list"])
        assert result.exit_code == 0
        assert "No labels found" in result.output


class TestNotificationCLI:
    """Tests for notification CLI commands."""

    def test_notification_help(self, runner: CliRunner) -> None:
        result = runner.invoke(notification, ["--help"])
        assert result.exit_code == 0
        assert "list" in result.output.lower()

    @patch("taskflow.cli.notification_commands.NotificationService")
    def test_list_notifications(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.get_user_notifications.return_value = []
        mock_service_cls.return_value = mock_service

        result = runner.invoke(notification, ["list", "-u", "alice"])
        assert result.exit_code == 0
        assert "No notifications found" in result.output

    @patch("taskflow.cli.notification_commands.NotificationService")
    def test_unread_count(self, mock_service_cls, runner: CliRunner) -> None:
        mock_service = MagicMock()
        mock_service.get_unread_count.return_value = 3
        mock_service_cls.return_value = mock_service

        result = runner.invoke(notification, ["unread-count", "-u", "alice"])
        assert result.exit_code == 0
        assert "3" in result.output
