# tests/unit/test_table_generator.py
"""Tests for table mesh generator."""

import random

import trimesh

from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from geometry.generators.table_generator import generate_table_mesh


def test_generates_trimesh():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)


def test_mesh_has_vertices_and_faces():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0


def test_mesh_is_deterministic():
    g1 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    g2 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    m1 = generate_table_mesh(g1)
    m2 = generate_table_mesh(g2)
    assert len(m1.vertices) == len(m2.vertices)


def test_multiple_seeds_produce_different_meshes():
    g1 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(1))
    g2 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(2))
    m1 = generate_table_mesh(g1)
    m2 = generate_table_mesh(g2)
    if len(m1.vertices) != len(m2.vertices):
        return  # different vertex counts proves meshes differ
    assert not (m1.vertices == m2.vertices).all()


def test_mesh_has_positive_volume():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    assert mesh.volume > 0


def test_pedestal_table():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    genome.genes["support_strategy"] = "pedestal"
    genome.genes["support_count"] = 1
    mesh = generate_table_mesh(genome)
    assert isinstance(mesh, trimesh.Trimesh)
    assert len(mesh.vertices) > 0
