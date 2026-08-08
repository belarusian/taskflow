"""Base file storage for persisting data to disk."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class FileStore:
    """Base class for file-based storage with JSON serialization."""

    def __init__(self, storage_dir: str = "~/.taskflow") -> None:
        """Initialize storage directory."""
        self.storage_dir = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, filename: str) -> Path:
        """Get full path for a storage file."""
        return self.storage_dir / filename

    def _read_json(self, filename: str) -> Any:
        """Read and parse a JSON file."""
        filepath = self._get_file_path(filename)
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, filename: str, data: Any) -> None:
        """Write data to a JSON file."""
        filepath = self._get_file_path(filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    def _file_exists(self, filename: str) -> bool:
        """Check if a storage file exists."""
        return self._get_file_path(filename).exists()

    def _delete_file(self, filename: str) -> bool:
        """Delete a storage file."""
        filepath = self._get_file_path(filename)
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def list_files(self, pattern: str = "*.json") -> list[str]:
        """List all files matching a pattern in storage directory."""
        return [f.name for f in self.storage_dir.glob(pattern)]
