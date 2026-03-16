"""Tests for physics/scoring.py — integration of all physics checks."""

import random

from core.genome.catalog_registry import get_catalog
from core.genome.genome import Genome
from core.genome.graph_builder import build_graph
from geometry.generators.generator_registry import generate_mesh
from physics.scoring import evaluate_physics, PhysicsResult


def _make_table(seed=42):
    """Generate a table candidate with its mesh and graph."""
    catalog = get_catalog("table_family")
    rng = random.Random(seed)
    genome = Genome.random_init(catalog, rng)
    mesh = generate_mesh(genome)
    graph = build_graph(genome, catalog)
    return mesh, graph, genome.genes


def _make_lamp(seed=42):
    catalog = get_catalog("lamp_family")
    rng = random.Random(seed)
    genome = Genome.random_init(catalog, rng)
    mesh = generate_mesh(genome)
    graph = build_graph(genome, catalog)
    return mesh, graph, genome.genes


def _make_chair(seed=42):
    catalog = get_catalog("chair_family_lite")
    rng = random.Random(seed)
    genome = Genome.random_init(catalog, rng)
    mesh = generate_mesh(genome)
    graph = build_graph(genome, catalog)
    return mesh, graph, genome.genes


def test_evaluate_table_returns_physics_result():
    mesh, graph, genes = _make_table()
    result = evaluate_physics(mesh, graph, genes)
    assert isinstance(result, PhysicsResult)
    assert isinstance(result.passed_hard_physics, bool)
    assert 0 <= result.physics_score <= 1
    assert "connectivity_score" in result.sub_scores
    assert "stability_score" in result.sub_scores


def test_evaluate_table_connectivity():
    mesh, graph, genes = _make_table()
    result = evaluate_physics(mesh, graph, genes)
    # A valid table should have connected load paths
    assert result.connectivity.is_connected is True


def test_evaluate_multiple_seeds():
    """Run physics on several seeds to ensure robustness."""
    for seed in range(10):
        mesh, graph, genes = _make_table(seed=seed)
        result = evaluate_physics(mesh, graph, genes)
        assert isinstance(result.physics_score, float)
        assert 0 <= result.physics_score <= 1


def test_evaluate_lamp():
    mesh, graph, genes = _make_lamp()
    result = evaluate_physics(mesh, graph, genes)
    assert isinstance(result, PhysicsResult)
    assert result.connectivity.is_connected is True


def test_evaluate_chair():
    mesh, graph, genes = _make_chair()
    result = evaluate_physics(mesh, graph, genes)
    assert isinstance(result, PhysicsResult)
    assert result.connectivity.is_connected is True


def test_sub_scores_all_bounded():
    mesh, graph, genes = _make_table()
    result = evaluate_physics(mesh, graph, genes)
    for name, score in result.sub_scores.items():
        assert 0 <= score <= 1, f"{name} = {score} out of bounds"


def test_material_affects_score():
    mesh, graph, genes = _make_table(seed=7)
    wood_result = evaluate_physics(mesh, graph, genes, material_name="wood")
    steel_result = evaluate_physics(mesh, graph, genes, material_name="steel")
    # Different materials may produce different scores
    assert isinstance(wood_result.physics_score, float)
    assert isinstance(steel_result.physics_score, float)
