# geometry/mesh_validation/validator.py
"""Mesh validation and reporting."""

from __future__ import annotations

from dataclasses import dataclass

import trimesh

from config.schemas.config_models import BuildVolume


@dataclass
class MeshReport:
    """Result of mesh validation checks."""

    has_vertices: bool = False
    has_faces: bool = False
    positive_volume: bool = False
    is_watertight: bool = False
    within_build_volume: bool = True
    vertex_count: int = 0
    face_count: int = 0
    volume: float = 0.0

    @property
    def is_acceptable(self) -> bool:
        """Minimum viability: has geometry with positive volume."""
        return self.has_vertices and self.has_faces and self.positive_volume

    def __str__(self) -> str:
        status = "PASS" if self.is_acceptable else "FAIL"
        return (
            f"MeshReport({status}): {self.vertex_count} vertices, "
            f"{self.face_count} faces, volume={self.volume:.1f}, "
            f"watertight={self.is_watertight}, build_vol={self.within_build_volume}"
        )


def validate_mesh(
    mesh: trimesh.Trimesh,
    build_volume: BuildVolume | None = None,
) -> MeshReport:
    """Run validation checks on a mesh and return a report."""
    report = MeshReport()

    report.has_vertices = len(mesh.vertices) > 0
    report.has_faces = len(mesh.faces) > 0
    report.vertex_count = len(mesh.vertices)
    report.face_count = len(mesh.faces)

    if report.has_vertices and report.has_faces:
        try:
            report.volume = float(mesh.volume)
            report.positive_volume = report.volume > 0
        except Exception:
            report.volume = 0.0
            report.positive_volume = False

        report.is_watertight = bool(mesh.is_watertight)

    if build_volume and report.has_vertices:
        extents = mesh.bounding_box.extents
        report.within_build_volume = (
            extents[0] <= build_volume.x
            and extents[1] <= build_volume.y
            and extents[2] <= build_volume.z
        )

    return report
