# geometry/primitives/primitives.py
"""Primitive mesh factories.

Each factory returns a watertight trimesh.Trimesh positioned at the
specified center. All dimensions are in mm.
"""

from __future__ import annotations

import numpy as np
import trimesh


def make_box(
    width: float, depth: float, height: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> trimesh.Trimesh:
    """Create a box (rectangular prism) centered at `center`."""
    mesh = trimesh.creation.box(extents=(width, depth, height))
    mesh.apply_translation(center)
    return mesh


def make_cylinder(
    radius: float, height: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    sections: int = 24,
) -> trimesh.Trimesh:
    """Create a cylinder centered at `center`, axis along Z."""
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation(center)
    return mesh


def make_frustum(
    r_bottom: float, r_top: float, height: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    sections: int = 24,
) -> trimesh.Trimesh:
    """Create a frustum (tapered cylinder) centered at `center`."""
    angles = np.linspace(0, 2 * np.pi, sections + 1)
    bottom_ring = np.column_stack([
        r_bottom * np.cos(angles[:-1]),
        r_bottom * np.sin(angles[:-1]),
        np.full(sections, -height / 2),
    ])
    top_ring = np.column_stack([
        r_top * np.cos(angles[:-1]),
        r_top * np.sin(angles[:-1]),
        np.full(sections, height / 2),
    ])

    vertices = np.vstack([bottom_ring, top_ring])
    n = sections
    faces = []

    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j])
        faces.append([i, n + j, n + i])

    bottom_center_idx = len(vertices)
    vertices = np.vstack([vertices, [[0, 0, -height / 2]]])
    for i in range(n):
        j = (i + 1) % n
        faces.append([bottom_center_idx, j, i])

    top_center_idx = len(vertices)
    vertices = np.vstack([vertices, [[0, 0, height / 2]]])
    for i in range(n):
        j = (i + 1) % n
        faces.append([top_center_idx, n + i, n + j])

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces))
    mesh.fix_normals()
    mesh.apply_translation(center)
    return mesh


def make_panel(
    width: float, height: float, thickness: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> trimesh.Trimesh:
    """Create a thin panel (width x thickness x height), upright along Z."""
    return make_box(width, thickness, height, center=center)
