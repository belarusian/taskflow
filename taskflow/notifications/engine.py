"""Notification engine for TaskFlow."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Optional

from taskflow.notifications.models import (
    Notification,
    NotificationPriority,
    NotificationType,
)

logger = logging.getLogger(__name__)

NotificationCallback = Callable[[Notification], None]


class NotificationEngine:
    """Engine for managing and dispatching notifications."""

    def __init__(self):
        """Initialize the notification engine."""
        self._notifications: list[Notification] = []
        self._callbacks: dict[NotificationType, list[NotificationCallback]] = (
            defaultdict(list)
        )
        self._user_notifications: dict[str, list[str]] = defaultdict(list)
        self._queue: asyncio.Queue[Notification] = asyncio.Queue()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    @property
    def notification_count(self) -> int:
        """Get total number of notifications."""
        return len(self._notifications)

    @property
    def unread_count(self) -> int:
        """Get count of unread notifications."""
        return sum(1 for n in self._notifications if not n.read)

    def on(
        self, notification_type: NotificationType
    ) -> Callable[[NotificationCallback], NotificationCallback]:
        """Decorator to register a callback for a notification type.

        Args:
            notification_type: The notification type to listen for.

        Returns:
            Decorator function.
        """
        def decorator(callback: NotificationCallback) -> NotificationCallback:
            self._callbacks[notification_type].append(callback)
            logger.debug(
                f"Registered callback for {notification_type.value}"
            )
            return callback
        return decorator

    def register_callback(
        self,
        notification_type: NotificationType,
        callback: NotificationCallback,
    ) -> None:
        """Register a callback for a notification type.

        Args:
            notification_type: The notification type.
            callback: The callback function.
        """
        self._callbacks[notification_type].append(callback)

    def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        recipient: Optional[str] = None,
        sender: Optional[str] = None,
        ticket_id: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Optional[dict] = None,
    ) -> Notification:
        """Create and dispatch a notification.

        Args:
            notification_type: The type of notification.
            title: Notification title.
            message: Notification message body.
            recipient: Optional recipient user.
            sender: Optional sender user.
            ticket_id: Optional related ticket ID.
            priority: Notification priority.
            metadata: Optional additional metadata.

        Returns:
            The created notification.
        """
        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            recipient=recipient,
            sender=sender,
            ticket_id=ticket_id,
            priority=priority,
            metadata=metadata or {},
        )

        self._notifications.append(notification)
        if recipient:
            self._user_notifications[recipient].append(notification.id)

        logger.info(
            f"Notification created: {notification_type.value} "
            f"for {recipient or 'all'}"
        )

        # Dispatch to callbacks
        for callback in self._callbacks.get(notification_type, []):
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        # Also dispatch to generic callbacks
        for callback in self._callbacks.get(NotificationType.SYSTEM, []):
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Generic callback error: {e}")

        return notification

    def get_notifications(
        self,
        user: Optional[str] = None,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications with optional filters.

        Args:
            user: Filter by recipient.
            unread_only: Only return unread notifications.
            notification_type: Filter by notification type.
            limit: Maximum number of notifications to return.

        Returns:
            List of matching notifications.
        """
        results = self._notifications

        if user:
            user_ids = self._user_notifications.get(user, [])
            results = [n for n in results if n.id in user_ids]

        if unread_only:
            results = [n for n in results if not n.read]

        if notification_type:
            results = [n for n in results if n.type == notification_type]

        results.sort(key=lambda n: n.created_at, reverse=True)
        return results[:limit]

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read.

        Args:
            notification_id: The notification ID.

        Returns:
            True if the notification was found and marked.
        """
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.read = True
                logger.debug(f"Notification {notification_id} marked as read")
                return True
        return False

    def mark_all_as_read(self, user: str) -> int:
        """Mark all notifications for a user as read.

        Args:
            user: The user whose notifications to mark as read.

        Returns:
            Number of notifications marked as read.
        """
        count = 0
        user_ids = self._user_notifications.get(user, [])
        for notification in self._notifications:
            if notification.id in user_ids and not notification.read:
                notification.read = True
                count += 1
        logger.info(f"Marked {count} notifications as read for {user}")
        return count

    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification.

        Args:
            notification_id: The notification ID.

        Returns:
            True if the notification was deleted.
        """
        for i, notification in enumerate(self._notifications):
            if notification.id == notification_id:
                self._notifications.pop(i)
                # Remove from user tracking
                for user, ids in self._user_notifications.items():
                    if notification_id in ids:
                        ids.remove(notification_id)
                logger.debug(f"Notification {notification_id} deleted")
                return True
        return False

    def clear_old_notifications(self, days: int = 30) -> int:
        """Clear notifications older than specified days.

        Args:
            days: Number of days to keep.

        Returns:
            Number of notifications cleared.
        """
        cutoff = datetime.now(timezone.utc)
        from datetime import timedelta

        cutoff -= timedelta(days=days)
        original_count = len(self._notifications)
        self._notifications = [
            n for n in self._notifications if n.created_at > cutoff
        ]
        cleared = original_count - len(self._notifications)
        logger.info(f"Cleared {cleared} old notifications")
        return cleared

    async def start_queue_processor(self) -> None:
        """Start the async notification queue processor."""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_queue())
        logger.info("Notification queue processor started")

    async def stop_queue_processor(self) -> None:
        """Stop the async notification queue processor."""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            logger.info("Notification queue processor stopped")

    async def _process_queue(self) -> None:
        """Process notifications from the async queue."""
        while self._running:
            try:
                notification = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                await self._dispatch_async(notification)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def _dispatch_async(self, notification: Notification) -> None:
        """Asynchronously dispatch a notification."""
        for callback in self._callbacks.get(notification.type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"Async callback error: {e}")
