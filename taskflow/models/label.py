"""Label model for categorizing tickets."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Label:
    """Represents a label/category for tickets."""

    name: str
    color: str = "#666666"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Valid hex color patterns
    VALID_COLORS = (
        "#000000", "#FF0000", "#00FF00", "#0000FF", "#FFFF00",
        "#FF00FF", "#00FFFF", "#FFFFFF", "#FF6600", "#9900FF",
        "#0099FF", "#FF0099", "#666666", "#333333", "#CCCCCC",
        "#FF3333", "#33FF33", "#3333FF", "#FFCC00", "#CC00FF",
    )

    def __post_init__(self) -> None:
        """Validate label name and color."""
        if not self.name or not self.name.strip():
            raise ValueError("Label name cannot be empty")
        self.name = self.name.strip().lower().replace(" ", "-")
        if not self.color.startswith("#"):
            self.color = "#666666"

    def __repr__(self) -> str:
        return f"Label(name={self.name!r}, color={self.color!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Label):
            return self.name == other.name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)
