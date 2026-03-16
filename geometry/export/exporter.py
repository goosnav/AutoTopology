# geometry/export/exporter.py
"""Export meshes to STL and metadata to JSON."""

from __future__ import annotations

import json
from pathlib import Path

import trimesh

from core.exceptions import ExportError


def export_stl(
    mesh: trimesh.Trimesh,
    path: Path,
    metadata: dict | None = None,
    metadata_path: Path | None = None,
) -> None:
    """Export mesh as binary STL. Optionally write metadata JSON."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(str(path), file_type="stl")

        if metadata and metadata_path:
            metadata_path = Path(metadata_path)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata, indent=2, default=str))
    except Exception as e:
        raise ExportError(f"STL export failed: {e}", details={"path": str(path)}) from e
