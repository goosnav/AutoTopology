# tests/unit/test_lamp_chair_generators.py
"""Tests for lamp and chair mesh generators + registry."""

import random

import trimesh

from core.genome.genome import Genome
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.chair_genes import CHAIR_GENE_CATALOG
from geometry.generators.lamp_generator import generate_lamp_mesh
from geometry.generators.chair_generator import generate_chair_mesh
from geometry.generators.generator_registry import generate_mesh


def test_lamp_generates_trimesh():
    genome = Genome.random_init(LAMP_GENE_CATALOG, random.Random(42))
    mesh = generate_lamp_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)
    assert len(mesh.vertices) > 0


def test_lamp_has_positive_volume():
    genome = Genome.random_init(LAMP_GENE_CATALOG, random.Random(42))
    mesh = generate_lamp_mesh(genome)
    assert mesh.volume > 0


def test_chair_generates_trimesh():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    mesh = generate_chair_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)
    assert len(mesh.vertices) > 0


def test_chair_has_positive_volume():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    mesh = generate_chair_mesh(genome)
    assert mesh.volume > 0


def test_chair_with_back_and_arms():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    genome.genes["back_present"] = True
    genome.genes["arm_present"] = True
    mesh = generate_chair_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)


def test_chair_stool_no_back():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    genome.genes["back_present"] = False
    genome.genes["arm_present"] = False
    mesh = generate_chair_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)


def test_registry_table():
    from core.genome.table_genes import TABLE_GENE_CATALOG
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)


def test_registry_lamp():
    genome = Genome.random_init(LAMP_GENE_CATALOG, random.Random(42))
    mesh = generate_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)


def test_registry_chair():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    mesh = generate_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)


def test_registry_unknown_family():
    import pytest
    genome = Genome(genes={"family_name": "unknown"})
    with pytest.raises(ValueError, match="Unknown family"):
        generate_mesh(genome)
