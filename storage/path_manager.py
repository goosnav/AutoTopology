"""Storage path manager: resolve, create, and sanitize project paths."""

from __future__ import annotations

import re
from pathlib import Path


class StorageManager:
    """Manages storage directories for a project.

    Resolves and creates subdirectories for checkpoints, cache, db, logs, exports.
    """

    SUBDIRS = ("checkpoints", "cache", "db", "logs", "exports")

    def __init__(self, project_root: Path):
        self._root = Path(project_root).resolve()
        self._storage = self._root / "storage"

    @property
    def root(self) -> Path:
        return self._root

    @property
    def storage(self) -> Path:
        return self._storage

    @property
    def checkpoints(self) -> Path:
        return self._storage / "checkpoints"

    @property
    def cache(self) -> Path:
        return self._storage / "cache"

    @property
    def db(self) -> Path:
        return self._storage / "db"

    @property
    def logs(self) -> Path:
        return self._storage / "logs"

    @property
    def exports(self) -> Path:
        return self._storage / "exports"

    def ensure_dirs(self) -> None:
        """Create all required storage directories."""
        for subdir in self.SUBDIRS:
            (self._storage / subdir).mkdir(parents=True, exist_ok=True)

    def resolve_path(self, relative: str) -> Path:
        """Resolve a relative path within the project root safely.

        Raises ValueError if the resolved path escapes the project root.
        """
        resolved = (self._root / relative).resolve()
        if not str(resolved).startswith(str(self._root)):
            raise ValueError(
                f"Path traversal detected: '{relative}' resolves outside project root"
            )
        return resolved

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Sanitize a filename by stripping path components and unsafe characters.

        Args:
            name: Raw filename.

        Returns:
            Safe filename string.
        """
        # Strip directory components
        name = Path(name).name
        # Remove anything that isn't alphanumeric, dash, underscore, or dot
        name = re.sub(r"[^\w\-.]", "_", name)
        # Prevent leading dots (hidden files)
        name = name.lstrip(".")
        # Fallback for empty
        if not name:
            name = "unnamed"
        return name
