"""Shared test fixtures for TaskFlow."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from taskflow.models.ticket import Priority, Status, Ticket
from taskflow.models.user import User
from taskflow.models.label import Label
from taskflow.models.notification import Notification, NotificationType
from taskflow.storage.ticket_store import TicketStore
from taskflow.storage.user_store import UserStore
from taskflow.storage.label_store import LabelStore
from taskflow.storage.notification_store import NotificationStore
from taskflow.services.ticket_service import TicketService
from taskflow.services.user_service import UserService
from taskflow.services.label_service import LabelService
from taskflow.services.notification_service import NotificationService


@pytest.fixture
def temp_storage_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def ticket_store(temp_storage_dir: str) -> TicketStore:
    """Create a ticket store with temp directory."""
    return TicketStore(storage_dir=temp_storage_dir)


@pytest.fixture
def user_store(temp_storage_dir: str) -> UserStore:
    """Create a user store with temp directory."""
    return UserStore(storage_dir=temp_storage_dir)


@pytest.fixture
def label_store(temp_storage_dir: str) -> LabelStore:
    """Create a label store with temp directory."""
    return LabelStore(storage_dir=temp_storage_dir)


@pytest.fixture
def notification_store(temp_storage_dir: str) -> NotificationStore:
    """Create a notification store with temp directory."""
    return NotificationStore(storage_dir=temp_storage_dir)


@pytest.fixture
def ticket_service(temp_storage_dir: str) -> TicketService:
    """Create a ticket service with temp storage."""
    return TicketService(store=TicketStore(storage_dir=temp_storage_dir))


@pytest.fixture
def user_service(temp_storage_dir: str) -> UserService:
    """Create a user service with temp storage."""
    return UserService(store=UserStore(storage_dir=temp_storage_dir))


@pytest.fixture
def label_service(temp_storage_dir: str) -> LabelService:
    """Create a label service with temp storage."""
    return LabelService(store=LabelStore(storage_dir=temp_storage_dir))


@pytest.fixture
def notification_service(temp_storage_dir: str) -> NotificationService:
    """Create a notification service with temp storage."""
    return NotificationService(store=NotificationStore(storage_dir=temp_storage_dir))


@pytest.fixture
def sample_ticket() -> Ticket:
    """Create a sample ticket for testing."""
    return Ticket(
        id="test123",
        title="Test Ticket",
        description="A test ticket",
        priority=Priority.HIGH,
        status=Status.TODO,
        labels=["bug", "frontend"],
        assignee="alice",
        reporter="bob",
    )


@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    return User(username="alice", email="alice@example.com", display_name="Alice Smith")


@pytest.fixture
def sample_label() -> Label:
    """Create a sample label for testing."""
    return Label(name="bug", color="#FF0000", description="Bug reports")
