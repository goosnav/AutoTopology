"""ExportService — export a candidate as metadata JSON (+ STL placeholder).

Spec §17.2: The user must be able to export any displayed candidate.
Full STL export requires a mesh; here we write metadata always and
attempt STL generation if geometry is available.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.evolution.candidate import Candidate


class ExportService:
    """Exports candidates to the configured export directory.

    Args:
        export_dir: Directory where export files are written.
    """

    def __init__(self, export_dir: Path) -> None:
        self._dir = Path(export_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #

    def export(self, candidate: Candidate) -> dict[str, Any]:
        """Export a candidate's metadata JSON (and STL if mesh available).

        Args:
            candidate: The candidate to export.

        Returns:
            Dict with keys:
            - candidate_id
            - metadata_path: path to the written JSON file (str)
            - stl_path: path to STL if generated, else None
        """
        cid = candidate.candidate_id
        meta_path = self._dir / f"{cid}_meta.json"

        # Build metadata payload
        meta: dict[str, Any] = {
            "candidate_id": cid,
            "family": candidate.family,
            "physics_score": candidate.physics_score,
            "aesthetic_score": candidate.aesthetic_score,
            "novelty_score": candidate.novelty_score,
            "is_valid": candidate.is_valid,
            "human_selected": candidate.human_selected,
            "genes": candidate.genome.genes,
            "genome_id": candidate.genome.genome_id,
            "metadata": candidate.metadata,
        }
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        stl_path: str | None = None

        # Attempt STL generation if geometry pipeline is available
        try:
            from geometry.generators.generator_registry import generate_mesh
            from geometry.export.stl_exporter import export_stl

            mesh = generate_mesh(candidate.genome)
            stl_file = self._dir / f"{cid}.stl"
            export_stl(mesh, stl_file)
            stl_path = str(stl_file)
        except Exception:
            # STL generation is best-effort; metadata always written
            pass

        return {
            "candidate_id": cid,
            "metadata_path": str(meta_path),
            "stl_path": stl_path,
        }
