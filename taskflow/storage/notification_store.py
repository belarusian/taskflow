"""Notification storage for managing user notifications."""

from __future__ import annotations

from typing import Optional

from taskflow.models.notification import Notification, NotificationType
from taskflow.storage.file_store import FileStore


class NotificationStore(FileStore):
    """Persistent storage for notifications."""

    NOTIFICATIONS_FILE = "notifications.json"

    def _load_notifications(self) -> dict[str, dict]:
        """Load all notifications from storage."""
        data = self._read_json(self.NOTIFICATIONS_FILE)
        return data if isinstance(data, dict) else {}

    def _save_notifications(self, notifications: dict[str, dict]) -> None:
        """Save all notifications to storage."""
        self._write_json(self.NOTIFICATIONS_FILE, notifications)

    def create(self, notification: Notification) -> Notification:
        """Create and persist a new notification."""
        notifications = self._load_notifications()
        notifications[notification.id] = notification.to_dict()
        self._save_notifications(notifications)
        return notification

    def get(self, notification_id: str) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        notifications = self._load_notifications()
        data = notifications.get(notification_id)
        if data is None:
            return None
        return Notification(**data)

    def get_for_user(self, username: str) -> list[Notification]:
        """Get all notifications for a specific user."""
        notifications = self._load_notifications()
        return [
            Notification(**data)
            for data in notifications.values()
            if data.get("recipient") == username
        ]

    def get_unread(self, username: str) -> list[Notification]:
        """Get unread notifications for a user."""
        return [
            n for n in self.get_for_user(username) if not n.is_read
        ]

    def mark_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        notifications = self._load_notifications()
        if notification_id not in notifications:
            return False
        notif = Notification(**notifications[notification_id])
        notif.mark_read()
        notifications[notification_id] = notif.to_dict()
        self._save_notifications(notifications)
        return True

    def mark_all_read(self, username: str) -> int:
        """Mark all notifications for a user as read. Returns count."""
        notifications = self._load_notifications()
        count = 0
        for nid, data in notifications.items():
            if data.get("recipient") == username and not data.get("is_read"):
                notif = Notification(**data)
                notif.mark_read()
                notifications[nid] = notif.to_dict()
                count += 1
        self._save_notifications(notifications)
        return count

    def delete(self, notification_id: str) -> bool:
        """Delete a notification by ID."""
        notifications = self._load_notifications()
        if notification_id not in notifications:
            return False
        del notifications[notification_id]
        self._save_notifications(notifications)
        return True

    def delete_for_user(self, username: str) -> int:
        """Delete all notifications for a user. Returns count."""
        notifications = self._load_notifications()
        to_delete = [
            nid for nid, data in notifications.items()
            if data.get("recipient") == username
        ]
        for nid in to_delete:
            del notifications[nid]
        self._save_notifications(notifications)
        return len(to_delete)

    def filter_by_type(self, notification_type: NotificationType) -> list[Notification]:
        """Filter notifications by type."""
        notifications = self._load_notifications()
        return [
            Notification(**data)
            for data in notifications.values()
            if data.get("type") == notification_type.value
        ]
