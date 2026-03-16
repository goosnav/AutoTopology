# tests/integration/test_geometry_batch.py
"""Batch validation: random genomes should produce valid meshes at >90% rate."""

import random

import pytest

from core.genome.genome import Genome
from core.genome.catalog_registry import get_catalog
from geometry.generators.generator_registry import generate_mesh
from geometry.mesh_validation.validator import validate_mesh


@pytest.mark.parametrize("family", ["table_family", "lamp_family", "chair_family_lite"])
def test_batch_generation_success_rate(family):
    """Generate 50 random candidates and verify >90% produce valid meshes."""
    catalog = get_catalog(family)
    n_total = 50
    n_valid = 0

    for seed in range(n_total):
        try:
            genome = Genome.random_init(catalog, random.Random(seed))
            mesh = generate_mesh(genome)
            report = validate_mesh(mesh)
            if report.is_acceptable:
                n_valid += 1
        except Exception:
            pass

    rate = n_valid / n_total
    assert rate >= 0.9, f"{family}: {n_valid}/{n_total} valid ({rate:.0%}), need >90%"
