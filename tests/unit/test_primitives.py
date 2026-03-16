# tests/unit/test_primitives.py
"""Tests for primitive mesh factories."""

import numpy as np
import trimesh

from geometry.primitives.primitives import make_box, make_cylinder, make_frustum, make_panel


def test_make_box_dimensions():
    mesh = make_box(100, 200, 50)
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents, [100, 200, 50], atol=0.1)


def test_make_box_is_watertight():
    mesh = make_box(100, 200, 50)
    assert mesh.is_watertight


def test_make_box_with_position():
    mesh = make_box(100, 100, 100, center=(50, 50, 50))
    centroid = mesh.centroid
    np.testing.assert_allclose(centroid, [50, 50, 50], atol=0.1)


def test_make_cylinder_is_watertight():
    mesh = make_cylinder(radius=20, height=100)
    assert mesh.is_watertight


def test_make_cylinder_dimensions():
    mesh = make_cylinder(radius=25, height=200)
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents[2], 200, atol=1.0)
    np.testing.assert_allclose(extents[0], 50, atol=2.0)


def test_make_frustum_is_watertight():
    mesh = make_frustum(r_bottom=30, r_top=20, height=100)
    assert mesh.is_watertight


def test_make_frustum_with_taper():
    mesh = make_frustum(r_bottom=40, r_top=10, height=150)
    assert mesh.is_watertight
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents[2], 150, atol=1.0)


def test_make_panel_is_watertight():
    mesh = make_panel(width=200, height=300, thickness=10)
    assert mesh.is_watertight


def test_make_panel_dimensions():
    mesh = make_panel(width=200, height=300, thickness=10)
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents, [200, 10, 300], atol=0.1)


def test_make_cylinder_with_position():
    mesh = make_cylinder(radius=20, height=100, center=(100, 200, 50))
    centroid = mesh.centroid
    np.testing.assert_allclose(centroid, [100, 200, 50], atol=1.0)
