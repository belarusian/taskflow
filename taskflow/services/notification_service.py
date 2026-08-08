"""Notification service with real-time event handling."""

from __future__ import annotations

from typing import Optional

from taskflow.models.notification import Notification, NotificationType
from taskflow.models.ticket import Ticket
from taskflow.storage.notification_store import NotificationStore


class NotificationService:
    """Service layer for notification management and dispatch."""

    def __init__(self, store: Optional[NotificationStore] = None) -> None:
        """Initialize with optional store instance."""
        self.store = store or NotificationStore()

    def create_notification(
        self,
        title: str,
        message: str,
        recipient: Optional[str] = None,
        sender: Optional[str] = None,
        ticket_id: Optional[str] = None,
        notification_type: NotificationType = NotificationType.SYSTEM,
    ) -> Notification:
        """Create and persist a notification."""
        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            recipient=recipient,
            sender=sender,
            ticket_id=ticket_id,
        )
        return self.store.create(notification)

    def notify_ticket_created(self, ticket: Ticket, reporter: Optional[str] = None) -> list[Notification]:
        """Create notifications when a ticket is created."""
        notifications = []
        # Notify assignee if set
        if ticket.assignee:
            notif = self.create_notification(
                title=f"New ticket assigned: {ticket.title}",
                message=f"Ticket {ticket.id} has been assigned to you.",
                recipient=ticket.assignee,
                sender=reporter,
                ticket_id=ticket.id,
                notification_type=NotificationType.TICKET_ASSIGNED,
            )
            notifications.append(notif)
        # Create a general notification
        general = self.create_notification(
            title=f"Ticket created: {ticket.title}",
            message=f"New ticket {ticket.id} created by {reporter or 'system'}.",
            ticket_id=ticket.id,
            notification_type=NotificationType.TICKET_CREATED,
        )
        notifications.append(general)
        return notifications

    def notify_ticket_updated(self, ticket: Ticket, updater: Optional[str] = None) -> Notification:
        """Create notification when a ticket is updated."""
        return self.create_notification(
            title=f"Ticket updated: {ticket.title}",
            message=f"Ticket {ticket.id} was updated by {updater or 'system'}.",
            recipient=ticket.assignee,
            sender=updater,
            ticket_id=ticket.id,
            notification_type=NotificationType.TICKET_UPDATED,
        )

    def notify_ticket_assigned(
        self,
        ticket: Ticket,
        assignee: str,
        assigner: Optional[str] = None,
    ) -> Notification:
        """Create notification when a ticket is assigned."""
        return self.create_notification(
            title=f"Ticket assigned: {ticket.title}",
            message=f"Ticket {ticket.id} has been assigned to you by {assigner or 'system'}.",
            recipient=assignee,
            sender=assigner,
            ticket_id=ticket.id,
            notification_type=NotificationType.TICKET_ASSIGNED,
        )

    def notify_status_change(
        self,
        ticket: Ticket,
        old_status: str,
        new_status: str,
        changer: Optional[str] = None,
    ) -> Notification:
        """Create notification when ticket status changes."""
        return self.create_notification(
            title=f"Status changed: {ticket.title}",
            message=f"Ticket {ticket.id} status changed from {old_status} to {new_status}.",
            recipient=ticket.assignee,
            sender=changer,
            ticket_id=ticket.id,
            notification_type=NotificationType.TICKET_STATUS_CHANGED,
        )

    def notify_mention(
        self,
        mentioned_user: str,
        ticket_id: str,
        mentioner: str,
        context: str = "",
    ) -> Notification:
        """Create notification when a user is mentioned."""
        return self.create_notification(
            title=f"You were mentioned in ticket {ticket_id}",
            message=f"{mentioner} mentioned you: {context}",
            recipient=mentioned_user,
            sender=mentioner,
            ticket_id=ticket_id,
            notification_type=NotificationType.USER_MENTIONED,
        )

    def get_user_notifications(self, username: str) -> list[Notification]:
        """Get all notifications for a user."""
        return self.store.get_for_user(username)

    def get_unread_notifications(self, username: str) -> list[Notification]:
        """Get unread notifications for a user."""
        return self.store.get_unread(username)

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        return self.store.mark_read(notification_id)

    def mark_all_read(self, username: str) -> int:
        """Mark all user notifications as read."""
        return self.store.mark_all_read(username)

    def get_unread_count(self, username: str) -> int:
        """Get count of unread notifications for a user."""
        return len(self.store.get_unread(username))
