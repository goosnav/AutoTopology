"""PreferenceStore — JSONL persistence for pairwise preference data.

Spec §18.5: Store taste model artifacts; persist across sessions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PreferenceStore:
    """Append-only JSONL store for pairwise preference records.

    Each record is one JSON object per line.  The file is created on
    first write; missing files are treated as empty.

    Args:
        path: File path for the JSONL store.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    # ------------------------------------------------------------------ #

    def append(self, record: dict[str, Any]) -> None:
        """Append a single preference record.

        Args:
            record: Any JSON-serialisable dict.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_all(self) -> list[dict[str, Any]]:
        """Return all stored records.

        Returns:
            List of dicts.  Empty list if the file does not exist.
        """
        if not self._path.exists():
            return []
        records = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def count(self) -> int:
        """Number of stored records."""
        return len(self.load_all())

    def clear(self) -> None:
        """Delete all stored records."""
        if self._path.exists():
            self._path.unlink()
