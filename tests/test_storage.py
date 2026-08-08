"""Tests for TaskFlow storage layer."""

from datetime import datetime, timedelta

import pytest

from taskflow.models.ticket import Priority, Status, Ticket
from taskflow.models.user import User
from taskflow.models.label import Label
from taskflow.models.notification import Notification, NotificationType
from taskflow.storage.ticket_store import TicketStore
from taskflow.storage.user_store import UserStore
from taskflow.storage.label_store import LabelStore
from taskflow.storage.notification_store import NotificationStore


class TestTicketStore:
    """Tests for TicketStore."""

    def test_create_and_get(self, ticket_store: TicketStore) -> None:
        ticket = Ticket(title="Test Ticket")
        saved = ticket_store.create(ticket)
        loaded = ticket_store.get(ticket.id)
        assert loaded is not None
        assert loaded.title == "Test Ticket"

    def test_create_multiple(self, ticket_store: TicketStore) -> None:
        t1 = ticket_store.create(Ticket(title="First"))
        t2 = ticket_store.create(Ticket(title="Second"))
        assert ticket_store.count() == 2

    def test_update(self, ticket_store: TicketStore) -> None:
        ticket = ticket_store.create(Ticket(title="Original"))
        ticket.title = "Updated"
        updated = ticket_store.update(ticket)
        assert updated is not None
        assert updated.title == "Updated"

    def test_update_nonexistent(self, ticket_store: TicketStore) -> None:
        ticket = Ticket(id="nonexistent", title="Test")
        result = ticket_store.update(ticket)
        assert result is None

    def test_delete(self, ticket_store: TicketStore) -> None:
        ticket = ticket_store.create(Ticket(title="To Delete"))
        assert ticket_store.delete(ticket.id) is True
        assert ticket_store.get(ticket.id) is None

    def test_delete_nonexistent(self, ticket_store: TicketStore) -> None:
        assert ticket_store.delete("nonexistent") is False

    def test_list_all(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="A"))
        ticket_store.create(Ticket(title="B"))
        tickets = ticket_store.list_all()
        assert len(tickets) == 2

    def test_filter_by_status(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="A", status=Status.TODO))
        ticket_store.create(Ticket(title="B", status=Status.DONE))
        todos = ticket_store.filter_by_status(Status.TODO)
        assert len(todos) == 1
        assert todos[0].title == "A"

    def test_filter_by_priority(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="A", priority=Priority.HIGH))
        ticket_store.create(Ticket(title="B", priority=Priority.LOW))
        highs = ticket_store.filter_by_priority(Priority.HIGH)
        assert len(highs) == 1

    def test_filter_by_assignee(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="A", assignee="alice"))
        ticket_store.create(Ticket(title="B", assignee="bob"))
        alice_tickets = ticket_store.filter_by_assignee("alice")
        assert len(alice_tickets) == 1

    def test_filter_by_label(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="A", labels=["bug"]))
        ticket_store.create(Ticket(title="B", labels=["feature"]))
        bugs = ticket_store.filter_by_label("bug")
        assert len(bugs) == 1

    def test_search(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="Fix login bug", description="Critical issue"))
        ticket_store.create(Ticket(title="Add feature", description="Nice to have"))
        results = ticket_store.search("login")
        assert len(results) == 1
        assert results[0].title == "Fix login bug"

    def test_search_in_description(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="Something", description="Contains keyword"))
        results = ticket_store.search("keyword")
        assert len(results) == 1

    def test_get_unassigned(self, ticket_store: TicketStore) -> None:
        ticket_store.create(Ticket(title="A", assignee="alice"))
        ticket_store.create(Ticket(title="B"))
        unassigned = ticket_store.get_unassigned()
        assert len(unassigned) == 1

    def test_get_overdue(self, ticket_store: TicketStore) -> None:
        past = datetime.utcnow() - timedelta(days=1)
        ticket_store.create(Ticket(title="Overdue", due_date=past))
        ticket_store.create(Ticket(title="Not overdue"))
        overdue = ticket_store.get_overdue()
        assert len(overdue) == 1

    def test_empty_store(self, ticket_store: TicketStore) -> None:
        assert ticket_store.count() == 0
        assert ticket_store.list_all() == []


class TestUserStore:
    """Tests for UserStore."""

    def test_create_and_get(self, user_store: UserStore) -> None:
        user = User(username="alice")
        user_store.create(user)
        loaded = user_store.get("alice")
        assert loaded is not None
        assert loaded.username == "alice"

    def test_update(self, user_store: UserStore) -> None:
        user = User(username="alice")
        user_store.create(user)
        user.email = "new@example.com"
        updated = user_store.update(user)
        assert updated is not None
        assert updated.email == "new@example.com"

    def test_delete(self, user_store: UserStore) -> None:
        user_store.create(User(username="alice"))
        assert user_store.delete("alice") is True
        assert user_store.get("alice") is None

    def test_list_all(self, user_store: UserStore) -> None:
        user_store.create(User(username="alice"))
        user_store.create(User(username="bob"))
        users = user_store.list_all()
        assert len(users) == 2

    def test_get_active(self, user_store: UserStore) -> None:
        user_store.create(User(username="alice", is_active=True))
        user_store.create(User(username="bob", is_active=False))
        active = user_store.get_active()
        assert len(active) == 1
        assert active[0].username == "alice"

    def test_exists(self, user_store: UserStore) -> None:
        user_store.create(User(username="alice"))
        assert user_store.exists("alice") is True
        assert user_store.exists("nonexistent") is False


class TestLabelStore:
    """Tests for LabelStore."""

    def test_create_and_get(self, label_store: LabelStore) -> None:
        label = Label(name="bug", color="#FF0000")
        label_store.create(label)
        loaded = label_store.get("bug")
        assert loaded is not None
        assert loaded.color == "#FF0000"

    def test_delete(self, label_store: LabelStore) -> None:
        label_store.create(Label(name="bug"))
        assert label_store.delete("bug") is True
        assert label_store.get("bug") is None

    def test_list_all(self, label_store: LabelStore) -> None:
        label_store.create(Label(name="bug"))
        label_store.create(Label(name="feature"))
        labels = label_store.list_all()
        assert len(labels) == 2

    def test_exists(self, label_store: LabelStore) -> None:
        label_store.create(Label(name="bug"))
        assert label_store.exists("bug") is True
        assert label_store.exists("nonexistent") is False


class TestNotificationStore:
    """Tests for NotificationStore."""

    def test_create_and_get(self, notification_store: NotificationStore) -> None:
        notif = Notification(title="Test", message="Hello")
        notification_store.create(notif)
        loaded = notification_store.get(notif.id)
        assert loaded is not None
        assert loaded.title == "Test"

    def test_get_for_user(self, notification_store: NotificationStore) -> None:
        notification_store.create(Notification(title="A", recipient="alice"))
        notification_store.create(Notification(title="B", recipient="bob"))
        alice_notifs = notification_store.get_for_user("alice")
        assert len(alice_notifs) == 1

    def test_get_unread(self, notification_store: NotificationStore) -> None:
        n1 = Notification(title="Unread", recipient="alice", is_read=False)
        n2 = Notification(title="Read", recipient="alice", is_read=True)
        notification_store.create(n1)
        notification_store.create(n2)
        unread = notification_store.get_unread("alice")
        assert len(unread) == 1

    def test_mark_read(self, notification_store: NotificationStore) -> None:
        notif = Notification(title="Test", recipient="alice")
        notification_store.create(notif)
        assert notification_store.mark_read(notif.id) is True
        loaded = notification_store.get(notif.id)
        assert loaded.is_read is True

    def test_mark_all_read(self, notification_store: NotificationStore) -> None:
        notification_store.create(Notification(title="A", recipient="alice"))
        notification_store.create(Notification(title="B", recipient="alice"))
        notification_store.create(Notification(title="C", recipient="bob"))
        count = notification_store.mark_all_read("alice")
        assert count == 2

    def test_delete_for_user(self, notification_store: NotificationStore) -> None:
        notification_store.create(Notification(title="A", recipient="alice"))
        notification_store.create(Notification(title="B", recipient="alice"))
        notification_store.create(Notification(title="C", recipient="bob"))
        count = notification_store.delete_for_user("alice")
        assert count == 2

    def test_filter_by_type(self, notification_store: NotificationStore) -> None:
        notification_store.create(Notification(type=NotificationType.TICKET_CREATED))
        notification_store.create(Notification(type=NotificationType.USER_MENTIONED))
        created = notification_store.filter_by_type(NotificationType.TICKET_CREATED)
        assert len(created) == 1
