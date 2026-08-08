"""Validation utilities for TaskFlow."""

from __future__ import annotations

from taskflow.core.models import TicketPriority, TicketStatus


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_priority(value: str) -> TicketPriority:
    """Validate and convert a priority string to TicketPriority.

    Args:
        value: The priority string to validate.

    Returns:
        The corresponding TicketPriority enum value.

    Raises:
        ValidationError: If the priority value is invalid.
    """
    try:
        return TicketPriority(value.lower())
    except ValueError:
        valid = ", ".join(p.value for p in TicketPriority)
        raise ValidationError(
            f"Invalid priority '{value}'. Must be one of: {valid}"
        )


def validate_status(value: str) -> TicketStatus:
    """Validate and convert a status string to TicketStatus.

    Args:
        value: The status string to validate.

    Returns:
        The corresponding TicketStatus enum value.

    Raises:
        ValidationError: If the status value is invalid.
    """
    try:
        return TicketStatus(value.lower())
    except ValueError:
        valid = ", ".join(s.value for s in TicketStatus)
        raise ValidationError(
            f"Invalid status '{value}'. Must be one of: {valid}"
        )


def validate_ticket_title(title: str) -> str:
    """Validate a ticket title.

    Args:
        title: The title to validate.

    Returns:
        The validated title.

    Raises:
        ValidationError: If the title is invalid.
    """
    if not title or not title.strip():
        raise ValidationError("Title cannot be empty")
    if len(title) > 200:
        raise ValidationError("Title must be 200 characters or less")
    return title.strip()


def validate_assignee(assignee: str) -> str:
    """Validate an assignee name.

    Args:
        assignee: The assignee name to validate.

    Returns:
        The validated assignee name.

    Raises:
        ValidationError: If the assignee name is invalid.
    """
    if not assignee or not assignee.strip():
        raise ValidationError("Assignee name cannot be empty")
    if len(assignee) > 100:
        raise ValidationError("Assignee name must be 100 characters or less")
    return assignee.strip()


def validate_label_name(name: str) -> str:
    """Validate a label name.

    Args:
        name: The label name to validate.

    Returns:
        The validated label name.

    Raises:
        ValidationError: If the label name is invalid.
    """
    if not name or not name.strip():
        raise ValidationError("Label name cannot be empty")
    if len(name) > 50:
        raise ValidationError("Label name must be 50 characters or less")
    return name.strip()


def validate_color(color: str) -> str:
    """Validate a hex color string.

    Args:
        color: The color string to validate.

    Returns:
        The validated color string.

    Raises:
        ValidationError: If the color is invalid.
    """
    if not color.startswith("#"):
        raise ValidationError("Color must be a hex value starting with #")
    hex_part = color[1:]
    if len(hex_part) not in (3, 6):
        raise ValidationError("Color must be 3 or 6 hex digits")
    try:
        int(hex_part, 16)
    except ValueError:
        raise ValidationError("Color must contain only hex digits (0-9, a-f)")
    return color.lower()
