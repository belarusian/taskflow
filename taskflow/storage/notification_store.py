"""Notification storage for managing user notifications."""

from __future__ import annotations

from typing import Optional

from taskflow.models.notification import Notification, NotificationType, NotificationSeverity
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

    def _to_dict(self, notification: Notification) -> dict:
        """Convert notification to serializable dict."""
        return {
            "id": notification.id,
            "type": notification.type.value,
            "severity": notification.severity.value,
            "title": notification.title,
            "message": notification.message,
            "recipient": notification.recipient,
            "sender": notification.sender,
            "ticket_id": notification.ticket_id,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "metadata": notification.metadata,
        }

    def _from_dict(self, data: dict) -> Notification:
        """Convert dict to Notification, handling enum conversion."""
        if "type" in data and isinstance(data["type"], str):
            data["type"] = NotificationType(data["type"])
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = NotificationSeverity(data["severity"])
        return Notification(**data)

    def create(self, notification: Notification) -> Notification:
        """Create and persist a new notification."""
        notifications = self._load_notifications()
        notifications[notification.id] = self._to_dict(notification)
        self._save_notifications(notifications)
        return notification

    def get(self, notification_id: str) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        notifications = self._load_notifications()
        data = notifications.get(notification_id)
        if data is None:
            return None
        return self._from_dict(data)

    def get_for_user(self, username: str) -> list[Notification]:
        """Get all notifications for a specific user."""
        notifications = self._load_notifications()
        return [
            self._from_dict(data)
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
        notif = self._from_dict(notifications[notification_id])
        notif.mark_read()
        notifications[notification_id] = self._to_dict(notif)
        self._save_notifications(notifications)
        return True

    def mark_all_read(self, username: str) -> int:
        """Mark all notifications for a user as read. Returns count."""
        notifications = self._load_notifications()
        count = 0
        for nid, data in notifications.items():
            if data.get("recipient") == username and not data.get("is_read"):
                notif = self._from_dict(data)
                notif.mark_read()
                notifications[nid] = self._to_dict(notif)
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
            self._from_dict(data)
            for data in notifications.values()
            if data.get("type") == notification_type.value
        ]
