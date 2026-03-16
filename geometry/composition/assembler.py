# geometry/composition/assembler.py
"""Assemble multiple trimesh primitives into a single mesh."""

from __future__ import annotations

import trimesh


def assemble_meshes(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    """Concatenate meshes into a single combined mesh.

    Uses trimesh concatenation (vertex array stacking) rather than
    boolean operations to preserve watertightness of individual parts.
    """
    if not meshes:
        raise ValueError("No meshes to assemble")
    if len(meshes) == 1:
        return meshes[0].copy()
    return trimesh.util.concatenate(meshes)
