"""Tests for vision/collage/renderer.py and vision/collage/collage.py."""

import random

import numpy as np
import trimesh
from PIL import Image

from vision.collage.camera import get_four_view_transforms
from vision.collage.renderer import render_view, _render_wireframe
from vision.collage.collage import render_collage, render_and_save_collage
from core.genome.catalog_registry import get_catalog
from core.genome.genome import Genome
from geometry.generators.generator_registry import generate_mesh


def _make_box():
    return trimesh.primitives.Box(extents=[200, 200, 200])


def _make_table_mesh(seed=42):
    catalog = get_catalog("table_family")
    rng = random.Random(seed)
    genome = Genome.random_init(catalog, rng)
    return generate_mesh(genome)


# --- Wireframe renderer tests (always works, no GPU needed) ---

def test_wireframe_returns_image():
    mesh = _make_box()
    views = get_four_view_transforms(mesh)
    _, transform = views[0]
    img = _render_wireframe(mesh, transform, (256, 256))
    assert isinstance(img, Image.Image)
    assert img.size == (256, 256)


def test_wireframe_with_real_mesh():
    mesh = _make_table_mesh()
    views = get_four_view_transforms(mesh)
    _, transform = views[0]
    img = _render_wireframe(mesh, transform, (256, 256))
    assert isinstance(img, Image.Image)
    # Should have some non-background pixels (edges drawn)
    arr = np.array(img)
    # Check that not all pixels are identical (some edges were drawn)
    assert arr.std() > 0


def test_wireframe_empty_mesh():
    mesh = trimesh.Trimesh()
    transform = np.eye(4)
    img = _render_wireframe(mesh, transform, (256, 256))
    assert isinstance(img, Image.Image)
    assert img.size == (256, 256)


# --- render_view tests (uses best available backend) ---

def test_render_view_returns_image():
    mesh = _make_box()
    views = get_four_view_transforms(mesh)
    _, transform = views[0]
    img = render_view(mesh, transform, (256, 256))
    assert isinstance(img, Image.Image)
    assert img.size == (256, 256)


# --- Collage tests ---

def test_collage_returns_correct_size():
    mesh = _make_box()
    collage = render_collage(mesh, resolution_per_view=(128, 128), padding=4)
    assert isinstance(collage, Image.Image)
    assert collage.size == (128 * 2 + 4, 128 * 2 + 4)


def test_collage_with_real_mesh():
    mesh = _make_table_mesh()
    collage = render_collage(mesh, resolution_per_view=(128, 128))
    assert isinstance(collage, Image.Image)
    assert collage.size[0] > 0
    assert collage.size[1] > 0


def test_collage_deterministic():
    mesh = _make_table_mesh(seed=99)
    c1 = render_collage(mesh, resolution_per_view=(64, 64), draw_labels=False)
    c2 = render_collage(mesh, resolution_per_view=(64, 64), draw_labels=False)
    arr1 = np.array(c1)
    arr2 = np.array(c2)
    assert np.array_equal(arr1, arr2)


def test_save_collage(tmp_path):
    mesh = _make_table_mesh()
    out = tmp_path / "collage.png"
    result = render_and_save_collage(mesh, out, resolution_per_view=(64, 64))
    assert result.exists()
    assert result.suffix == ".png"
    img = Image.open(result)
    assert img.size == (64 * 2 + 4, 64 * 2 + 4)


def test_collage_no_labels():
    mesh = _make_box()
    collage = render_collage(mesh, resolution_per_view=(64, 64), draw_labels=False)
    assert isinstance(collage, Image.Image)
