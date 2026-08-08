"""Tests for TaskFlow data models."""

from datetime import datetime, timedelta

import pytest

from taskflow.models.ticket import Priority, Status, Ticket
from taskflow.models.user import User
from taskflow.models.label import Label
from taskflow.models.notification import Notification, NotificationType, NotificationSeverity


class TestPriority:
    """Tests for Priority enum."""

    def test_priority_values(self) -> None:
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.CRITICAL.value == "critical"

    def test_from_string_case_insensitive(self) -> None:
        assert Priority.from_string("HIGH") == Priority.HIGH
        assert Priority.from_string("low") == Priority.LOW
        assert Priority.from_string("Medium") == Priority.MEDIUM

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError):
            Priority.from_string("urgent")


class TestStatus:
    """Tests for Status enum."""

    def test_status_values(self) -> None:
        assert Status.TODO.value == "todo"
        assert Status.IN_PROGRESS.value == "in_progress"
        assert Status.IN_REVIEW.value == "in_review"
        assert Status.DONE.value == "done"
        assert Status.CANCELLED.value == "cancelled"

    def test_from_string_case_insensitive(self) -> None:
        assert Status.from_string("DONE") == Status.DONE
        assert Status.from_string("todo") == Status.TODO

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError):
            Status.from_string("pending")


class TestTicket:
    """Tests for Ticket model."""

    def test_create_ticket_minimal(self) -> None:
        ticket = Ticket(title="Test")
        assert ticket.title == "Test"
        assert ticket.priority == Priority.MEDIUM
        assert ticket.status == Status.TODO
        assert ticket.labels == []
        assert ticket.assignee is None
        assert len(ticket.id) == 12

    def test_create_ticket_full(self) -> None:
        ticket = Ticket(
            title="Full Ticket",
            description="Details here",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            labels=["bug"],
            assignee="alice",
        )
        assert ticket.title == "Full Ticket"
        assert ticket.priority == Priority.HIGH
        assert ticket.status == Status.IN_PROGRESS
        assert "bug" in ticket.labels

    def test_add_label(self) -> None:
        ticket = Ticket(title="Test")
        ticket.add_label("bug")
        assert "bug" in ticket.labels
        assert len(ticket.labels) == 1

    def test_add_duplicate_label(self) -> None:
        ticket = Ticket(title="Test")
        ticket.add_label("bug")
        ticket.add_label("bug")
        assert len(ticket.labels) == 1

    def test_remove_label(self) -> None:
        ticket = Ticket(title="Test", labels=["bug", "feature"])
        ticket.remove_label("bug")
        assert "bug" not in ticket.labels
        assert "feature" in ticket.labels

    def test_remove_nonexistent_label(self) -> None:
        ticket = Ticket(title="Test", labels=["bug"])
        ticket.remove_label("feature")
        assert "bug" in ticket.labels

    def test_update_status(self) -> None:
        ticket = Ticket(title="Test")
        ticket.update_status(Status.IN_PROGRESS)
        assert ticket.status == Status.IN_PROGRESS

    def test_assign_to(self) -> None:
        ticket = Ticket(title="Test")
        ticket.assign_to("alice")
        assert ticket.assignee == "alice"

    def test_unassign(self) -> None:
        ticket = Ticket(title="Test", assignee="alice")
        ticket.unassign()
        assert ticket.assignee is None

    def test_is_overdue_true(self) -> None:
        past = datetime.utcnow() - timedelta(days=1)
        ticket = Ticket(title="Test", due_date=past)
        assert ticket.is_overdue() is True

    def test_is_overdue_done(self) -> None:
        past = datetime.utcnow() - timedelta(days=1)
        ticket = Ticket(title="Test", due_date=past, status=Status.DONE)
        assert ticket.is_overdue() is False

    def test_is_overdue_no_due_date(self) -> None:
        ticket = Ticket(title="Test")
        assert ticket.is_overdue() is False

    def test_is_overdue_future(self) -> None:
        future = datetime.utcnow() + timedelta(days=1)
        ticket = Ticket(title="Test", due_date=future)
        assert ticket.is_overdue() is False

    def test_repr(self) -> None:
        ticket = Ticket(id="abc123", title="Test", priority=Priority.HIGH, status=Status.TODO)
        assert "abc123" in repr(ticket)
        assert "Test" in repr(ticket)

    def test_title_validation(self) -> None:
        with pytest.raises(Exception):
            Ticket(title="")

    def test_model_dump(self) -> None:
        ticket = Ticket(title="Test", priority=Priority.HIGH)
        data = ticket.model_dump()
        assert data["title"] == "Test"
        assert data["priority"] == "high"


class TestUser:
    """Tests for User model."""

    def test_create_user(self) -> None:
        user = User(username="alice", email="alice@example.com")
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.display_name == "Alice"
        assert user.is_active is True

    def test_display_name_from_username(self) -> None:
        user = User(username="john-doe")
        assert user.display_name == "John Doe"

    def test_empty_username_raises(self) -> None:
        with pytest.raises(ValueError):
            User(username="")

    def test_mark_seen(self) -> None:
        user = User(username="alice")
        user.mark_seen()
        assert user.last_seen is not None

    def test_increment_clients(self) -> None:
        user = User(username="alice")
        user.increment_clients()
        assert user.connected_clients == 1

    def test_decrement_clients(self) -> None:
        user = User(username="alice", connected_clients=2)
        user.decrement_clients()
        assert user.connected_clients == 1

    def test_decrement_clients_no_negative(self) -> None:
        user = User(username="alice", connected_clients=0)
        user.decrement_clients()
        assert user.connected_clients == 0

    def test_equality(self) -> None:
        u1 = User(username="alice")
        u2 = User(username="alice")
        assert u1 == u2

    def test_hash(self) -> None:
        users = {User(username="alice"), User(username="bob")}
        assert len(users) == 2


class TestLabel:
    """Tests for Label model."""

    def test_create_label(self) -> None:
        label = Label(name="bug", color="#FF0000")
        assert label.name == "bug"
        assert label.color == "#FF0000"

    def test_name_normalized(self) -> None:
        label = Label(name="Bug Fix")
        assert label.name == "bug-fix"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            Label(name="")

    def test_invalid_color_defaults(self) -> None:
        label = Label(name="test", color="invalid")
        assert label.color == "#666666"

    def test_equality(self) -> None:
        l1 = Label(name="bug")
        l2 = Label(name="bug")
        assert l1 == l2

    def test_hash(self) -> None:
        labels = {Label(name="bug"), Label(name="feature")}
        assert len(labels) == 2


class TestNotification:
    """Tests for Notification model."""

    def test_create_notification(self) -> None:
        notif = Notification(
            type=NotificationType.TICKET_CREATED,
            title="New Ticket",
            message="Ticket created",
        )
        assert notif.type == NotificationType.TICKET_CREATED
        assert notif.is_read is False

    def test_mark_read(self) -> None:
        notif = Notification(title="Test")
        notif.mark_read()
        assert notif.is_read is True
        assert notif.read_at is not None

    def test_to_dict(self) -> None:
        notif = Notification(
            type=NotificationType.TICKET_CREATED,
            title="Test",
            message="Msg",
        )
        data = notif.to_dict()
        assert data["type"] == "ticket_created"
        assert data["title"] == "Test"
        assert "created_at" in data

    def test_from_ticket_event(self) -> None:
        notif = Notification.from_ticket_event(
            event_type=NotificationType.TICKET_ASSIGNED,
            ticket_id="abc123",
            message="Assigned to you",
            sender="admin",
            recipient="alice",
        )
        assert notif.ticket_id == "abc123"
        assert notif.sender == "admin"
        assert notif.recipient == "alice"

    def test_notification_type_values(self) -> None:
        assert NotificationType.TICKET_CREATED.value == "ticket_created"
        assert NotificationType.USER_MENTIONED.value == "user_mentioned"

    def test_notification_severity(self) -> None:
        assert NotificationSeverity.INFO.value == "info"
        assert NotificationSeverity.WARNING.value == "warning"
        assert NotificationSeverity.IMPORTANT.value == "important"
