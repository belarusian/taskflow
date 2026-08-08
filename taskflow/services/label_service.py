"""Label service with business logic for label management."""

from __future__ import annotations

from typing import Optional

from taskflow.models.label import Label
from taskflow.storage.label_store import LabelStore


class LabelService:
    """Service layer for label operations."""

    def __init__(self, store: Optional[LabelStore] = None) -> None:
        """Initialize with optional store instance."""
        self.store = store or LabelStore()

    def create_label(
        self,
        name: str,
        color: str = "#666666",
        description: str = "",
    ) -> Label:
        """Create a new label."""
        if self.store.exists(name):
            raise ValueError(f"Label '{name}' already exists")
        label = Label(name=name, color=color, description=description)
        return self.store.create(label)

    def get_label(self, name: str) -> Optional[Label]:
        """Get a label by name."""
        return self.store.get(name)

    def update_label(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Label]:
        """Update label properties."""
        label = self.store.get(name)
        if label is None:
            return None
        if color is not None:
            label.color = color
        if description is not None:
            label.description = description
        return self.store.update(label)

    def delete_label(self, name: str) -> bool:
        """Delete a label."""
        return self.store.delete(name)

    def list_labels(self) -> list[Label]:
        """List all labels."""
        return self.store.list_all()
