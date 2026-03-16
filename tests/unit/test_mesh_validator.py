# tests/unit/test_mesh_validator.py
"""Tests for mesh validator."""

import random

import trimesh

from geometry.mesh_validation.validator import validate_mesh, MeshReport
from geometry.primitives.primitives import make_box
from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from geometry.generators.table_generator import generate_table_mesh


def test_valid_box():
    mesh = make_box(100, 100, 100)
    report = validate_mesh(mesh)
    assert report.has_vertices
    assert report.has_faces
    assert report.positive_volume


def test_report_from_table():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    report = validate_mesh(mesh)
    assert report.has_vertices
    assert report.has_faces
    assert report.positive_volume


def test_empty_mesh_fails():
    mesh = trimesh.Trimesh()
    report = validate_mesh(mesh)
    assert not report.has_vertices
    assert not report.is_acceptable


def test_report_str():
    mesh = make_box(100, 100, 100)
    report = validate_mesh(mesh)
    s = str(report)
    assert "vertices" in s.lower() or "volume" in s.lower()


def test_build_volume_check():
    from config.schemas.config_models import BuildVolume
    bv = BuildVolume(x=50, y=50, z=50)
    big_mesh = make_box(200, 200, 200)
    report = validate_mesh(big_mesh, build_volume=bv)
    assert not report.within_build_volume


def test_build_volume_passes():
    from config.schemas.config_models import BuildVolume
    bv = BuildVolume(x=500, y=500, z=500)
    small_mesh = make_box(100, 100, 100)
    report = validate_mesh(small_mesh, build_volume=bv)
    assert report.within_build_volume
