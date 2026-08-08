"""Label storage for managing ticket labels."""

from __future__ import annotations

from typing import Optional

from taskflow.models.label import Label
from taskflow.storage.file_store import FileStore


class LabelStore(FileStore):
    """Persistent storage for labels."""

    LABELS_FILE = "labels.json"

    def _load_labels(self) -> dict[str, dict]:
        """Load all labels from storage."""
        data = self._read_json(self.LABELS_FILE)
        return data if isinstance(data, dict) else {}

    def _save_labels(self, labels: dict[str, dict]) -> None:
        """Save all labels to storage."""
        self._write_json(self.LABELS_FILE, labels)

    def create(self, label: Label) -> Label:
        """Create and persist a new label."""
        labels = self._load_labels()
        labels[label.name] = label.__dict__
        self._save_labels(labels)
        return label

    def get(self, name: str) -> Optional[Label]:
        """Retrieve a label by name."""
        labels = self._load_labels()
        data = labels.get(name)
        if data is None:
            return None
        return Label(**data)

    def update(self, label: Label) -> Optional[Label]:
        """Update an existing label."""
        labels = self._load_labels()
        if label.name not in labels:
            return None
        labels[label.name] = label.__dict__
        self._save_labels(labels)
        return label

    def delete(self, name: str) -> bool:
        """Delete a label by name."""
        labels = self._load_labels()
        if name not in labels:
            return False
        del labels[name]
        self._save_labels(labels)
        return True

    def list_all(self) -> list[Label]:
        """List all labels."""
        labels = self._load_labels()
        return [Label(**data) for data in labels.values()]

    def exists(self, name: str) -> bool:
        """Check if a label exists."""
        return name in self._load_labels()
