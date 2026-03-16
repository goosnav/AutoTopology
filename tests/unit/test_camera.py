"""Tests for vision/collage/camera.py."""

import math

import numpy as np
import trimesh

from vision.collage.camera import (
    compute_camera_distance,
    camera_transform,
    get_four_view_transforms,
    VIEW_LABELS,
)


def _make_box(extents=(600, 400, 750)):
    return trimesh.primitives.Box(extents=extents)


def test_compute_camera_distance_positive():
    mesh = _make_box()
    dist = compute_camera_distance(mesh)
    assert dist > 0
    # Should be larger than the mesh extent
    assert dist > max(mesh.bounding_box.extents) / 2


def test_camera_distance_scales_with_mesh():
    small = _make_box((100, 100, 100))
    large = _make_box((1000, 1000, 1000))
    d_small = compute_camera_distance(small)
    d_large = compute_camera_distance(large)
    assert d_large > d_small


def test_camera_transform_is_4x4():
    t = camera_transform(0.0, 30.0, 500.0)
    assert t.shape == (4, 4)


def test_camera_transform_different_azimuths():
    t0 = camera_transform(0.0, 30.0, 500.0)
    t90 = camera_transform(90.0, 30.0, 500.0)
    # Different azimuths should produce different transforms
    assert not np.allclose(t0, t90)


def test_camera_position_at_correct_distance():
    dist = 500.0
    t = camera_transform(0.0, 0.0, dist, target=(0, 0, 0))
    pos = t[:3, 3]
    # At 0 elevation, 0 azimuth: camera on +Y axis
    actual_dist = np.linalg.norm(pos)
    assert abs(actual_dist - dist) < 1.0


def test_get_four_views_returns_four():
    mesh = _make_box()
    views = get_four_view_transforms(mesh)
    assert len(views) == 4
    labels = [v[0] for v in views]
    assert labels == list(VIEW_LABELS)


def test_four_views_are_all_different():
    mesh = _make_box()
    views = get_four_view_transforms(mesh)
    transforms = [v[1] for v in views]
    for i in range(len(transforms)):
        for j in range(i + 1, len(transforms)):
            assert not np.allclose(transforms[i], transforms[j])


def test_views_are_deterministic():
    mesh = _make_box()
    views1 = get_four_view_transforms(mesh)
    views2 = get_four_view_transforms(mesh)
    for (l1, t1), (l2, t2) in zip(views1, views2):
        assert l1 == l2
        assert np.allclose(t1, t2)
