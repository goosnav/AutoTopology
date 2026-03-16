# tests/unit/test_assembler.py
"""Tests for mesh assembler."""

import trimesh

from geometry.composition.assembler import assemble_meshes
from geometry.primitives.primitives import make_box, make_cylinder


def test_assemble_two_boxes():
    a = make_box(100, 100, 100, center=(0, 0, 50))
    b = make_box(20, 20, 200, center=(0, 0, 100))
    combined = assemble_meshes([a, b])
    assert isinstance(combined, trimesh.Trimesh)
    assert len(combined.vertices) == len(a.vertices) + len(b.vertices)


def test_assemble_single_mesh():
    a = make_box(100, 100, 100)
    combined = assemble_meshes([a])
    assert len(combined.vertices) == len(a.vertices)


def test_assemble_empty_list():
    import pytest
    with pytest.raises(ValueError, match="No meshes"):
        assemble_meshes([])


def test_assemble_preserves_faces():
    a = make_box(50, 50, 50)
    b = make_cylinder(10, 100)
    combined = assemble_meshes([a, b])
    assert len(combined.faces) == len(a.faces) + len(b.faces)
