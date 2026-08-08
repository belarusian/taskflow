"""Tests for TaskFlow service layer."""

from datetime import datetime

import pytest

from taskflow.models.ticket import Priority, Status
from taskflow.models.notification import NotificationType
from taskflow.services.ticket_service import TicketService
from taskflow.services.user_service import UserService
from taskflow.services.label_service import LabelService
from taskflow.services.notification_service import NotificationService


class TestTicketService:
    """Tests for TicketService."""

    def test_create_ticket(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(
            title="Test",
            priority="high",
            assignee="alice",
            labels=["bug"],
        )
        assert ticket.title == "Test"
        assert ticket.priority == Priority.HIGH
        assert ticket.assignee == "alice"
        assert "bug" in ticket.labels

    def test_create_ticket_with_due_date(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(
            title="Test",
            due_date="2025-12-31",
        )
        assert ticket.due_date is not None

    def test_get_ticket(self, ticket_service: TicketService) -> None:
        created = ticket_service.create_ticket(title="Test")
        found = ticket_service.get_ticket(created.id)
        assert found is not None
        assert found.title == "Test"

    def test_get_nonexistent_ticket(self, ticket_service: TicketService) -> None:
        assert ticket_service.get_ticket("nonexistent") is None

    def test_update_ticket_title(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Original")
        updated = ticket_service.update_ticket(ticket.id, title="Updated")
        assert updated is not None
        assert updated.title == "Updated"

    def test_update_ticket_status(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Test")
        updated = ticket_service.update_ticket(ticket.id, status="in_progress")
        assert updated is not None
        assert updated.status == Status.IN_PROGRESS

    def test_update_nonexistent(self, ticket_service: TicketService) -> None:
        result = ticket_service.update_ticket("nonexistent", title="X")
        assert result is None

    def test_delete_ticket(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Test")
        assert ticket_service.delete_ticket(ticket.id) is True
        assert ticket_service.get_ticket(ticket.id) is None

    def test_add_label(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Test")
        updated = ticket_service.add_label(ticket.id, "bug")
        assert updated is not None
        assert "bug" in updated.labels

    def test_remove_label(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Test", labels=["bug"])
        updated = ticket_service.remove_label(ticket.id, "bug")
        assert updated is not None
        assert "bug" not in updated.labels

    def test_assign_ticket(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Test")
        updated = ticket_service.assign_ticket(ticket.id, "alice")
        assert updated is not None
        assert updated.assignee == "alice"

    def test_unassign_ticket(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Test", assignee="alice")
        updated = ticket_service.unassign_ticket(ticket.id)
        assert updated is not None
        assert updated.assignee is None

    def test_change_status(self, ticket_service: TicketService) -> None:
        ticket = ticket_service.create_ticket(title="Test")
        updated = ticket_service.change_status(ticket.id, "done")
        assert updated is not None
        assert updated.status == Status.DONE

    def test_list_tickets(self, ticket_service: TicketService) -> None:
        ticket_service.create_ticket(title="A", priority="high")
        ticket_service.create_ticket(title="B", priority="low")
        all_tickets = ticket_service.list_tickets()
        assert len(all_tickets) == 2

    def test_list_filtered_by_status(self, ticket_service: TicketService) -> None:
        ticket_service.create_ticket(title="A", priority="high")
        ticket_service.create_ticket(title="B", priority="low")
        highs = ticket_service.list_tickets(priority="high")
        assert len(highs) == 1

    def test_list_filtered_by_assignee(self, ticket_service: TicketService) -> None:
        ticket_service.create_ticket(title="A", assignee="alice")
        ticket_service.create_ticket(title="B", assignee="bob")
        alice_tickets = ticket_service.list_tickets(assignee="alice")
        assert len(alice_tickets) == 1

    def test_search_tickets(self, ticket_service: TicketService) -> None:
        ticket_service.create_ticket(title="Fix bug")
        ticket_service.create_ticket(title="Add feature")
        results = ticket_service.search_tickets("bug")
        assert len(results) == 1

    def test_get_stats(self, ticket_service: TicketService) -> None:
        ticket_service.create_ticket(title="A", priority="high")
        ticket_service.create_ticket(title="B", priority="low", status="done")
        stats = ticket_service.get_stats()
        assert stats["total"] == 2
        assert stats["priority_high"] == 1
        assert stats["done"] == 1


class TestUserService:
    """Tests for UserService."""

    def test_create_user(self, user_service: UserService) -> None:
        user = user_service.create_user("alice", "alice@example.com")
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_create_duplicate_user_raises(self, user_service: UserService) -> None:
        user_service.create_user("alice")
        with pytest.raises(ValueError, match="already exists"):
            user_service.create_user("alice")

    def test_get_user(self, user_service: UserService) -> None:
        user_service.create_user("alice")
        user = user_service.get_user("alice")
        assert user is not None

    def test_get_nonexistent_user(self, user_service: UserService) -> None:
        assert user_service.get_user("nonexistent") is None

    def test_update_user(self, user_service: UserService) -> None:
        user_service.create_user("alice")
        updated = user_service.update_user("alice", email="new@example.com")
        assert updated is not None
        assert updated.email == "new@example.com"

    def test_delete_user(self, user_service: UserService) -> None:
        user_service.create_user("alice")
        assert user_service.delete_user("alice") is True

    def test_list_users(self, user_service: UserService) -> None:
        user_service.create_user("alice")
        user_service.create_user("bob")
        users = user_service.list_users()
        assert len(users) == 2

    def test_list_active_only(self, user_service: UserService) -> None:
        user_service.create_user("alice", is_active=True)
        user_service.create_user("bob", is_active=False)
        active = user_service.list_users(active_only=True)
        assert len(active) == 1


class TestLabelService:
    """Tests for LabelService."""

    def test_create_label(self, label_service: LabelService) -> None:
        label = label_service.create_label("bug", "#FF0000")
        assert label.name == "bug"
        assert label.color == "#FF0000"

    def test_create_duplicate_label_raises(self, label_service: LabelService) -> None:
        label_service.create_label("bug")
        with pytest.raises(ValueError, match="already exists"):
            label_service.create_label("bug")

    def test_get_label(self, label_service: LabelService) -> None:
        label_service.create_label("bug")
        label = label_service.get_label("bug")
        assert label is not None

    def test_delete_label(self, label_service: LabelService) -> None:
        label_service.create_label("bug")
        assert label_service.delete_label("bug") is True

    def test_list_labels(self, label_service: LabelService) -> None:
        label_service.create_label("bug")
        label_service.create_label("feature")
        labels = label_service.list_labels()
        assert len(labels) == 2


class TestNotificationService:
    """Tests for NotificationService."""

    def test_create_notification(self, notification_service: NotificationService) -> None:
        notif = notification_service.create_notification(
            title="Test",
            message="Hello",
            recipient="alice",
        )
        assert notif.title == "Test"
        assert notif.recipient == "alice"

    def test_notify_ticket_created(self, notification_service: NotificationService) -> None:
        from taskflow.models.ticket import Ticket
        ticket = Ticket(title="Test", assignee="alice")
        notifs = notification_service.notify_ticket_created(ticket, reporter="bob")
        assert len(notifs) >= 1

    def test_notify_ticket_assigned(self, notification_service: NotificationService) -> None:
        from taskflow.models.ticket import Ticket
        ticket = Ticket(title="Test")
        notif = notification_service.notify_ticket_assigned(
            ticket, assignee="alice", assigner="bob"
        )
        assert notif.recipient == "alice"
        assert notif.type == NotificationType.TICKET_ASSIGNED

    def test_get_unread_notifications(self, notification_service: NotificationService) -> None:
        notification_service.create_notification(
            title="A", message="M", recipient="alice"
        )
        unread = notification_service.get_unread_notifications("alice")
        assert len(unread) == 1

    def test_mark_as_read(self, notification_service: NotificationService) -> None:
        notif = notification_service.create_notification(
            title="Test", recipient="alice"
        )
        assert notification_service.mark_as_read(notif.id) is True

    def test_mark_all_read(self, notification_service: NotificationService) -> None:
        notification_service.create_notification(title="A", recipient="alice")
        notification_service.create_notification(title="B", recipient="alice")
        count = notification_service.mark_all_read("alice")
        assert count == 2

    def test_get_unread_count(self, notification_service: NotificationService) -> None:
        notification_service.create_notification(title="A", recipient="alice")
        assert notification_service.get_unread_count("alice") == 1

    def test_notify_mention(self, notification_service: NotificationService) -> None:
        notif = notification_service.notify_mention(
            mentioned_user="alice",
            ticket_id="abc123",
            mentioner="bob",
            context="Please review",
        )
        assert notif.recipient == "alice"
        assert notif.type == NotificationType.USER_MENTIONED
