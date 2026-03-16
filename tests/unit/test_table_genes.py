"""Tests for table family gene catalog."""

import random

from core.genome.table_genes import TABLE_GENE_CATALOG
from core.genome.genome import Genome
from core.genome.gene_types import GeneType


def test_catalog_has_all_layers():
    layers = {spec.layer for spec in TABLE_GENE_CATALOG}
    assert layers == {1, 2, 3, 4}


def test_catalog_layer1_has_family():
    l1_names = [s.name for s in TABLE_GENE_CATALOG if s.layer == 1]
    assert "family_name" in l1_names
    family_spec = next(s for s in TABLE_GENE_CATALOG if s.name == "family_name")
    assert "table_family" in family_spec.categories


def test_catalog_layer2_has_support_count():
    l2_names = [s.name for s in TABLE_GENE_CATALOG if s.layer == 2]
    assert "support_count" in l2_names


def test_catalog_layer3_has_dimensions():
    l3_names = [s.name for s in TABLE_GENE_CATALOG if s.layer == 3]
    assert "width" in l3_names
    assert "depth" in l3_names
    assert "height" in l3_names


def test_catalog_layer4_has_surface_genes():
    l4_names = [s.name for s in TABLE_GENE_CATALOG if s.layer == 4]
    assert "perforation_flag" in l4_names


def test_random_genome_from_catalog():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    assert genome.validate(TABLE_GENE_CATALOG) is True


def test_all_specs_have_defaults():
    for spec in TABLE_GENE_CATALOG:
        assert spec.default is not None, f"{spec.name} missing default"


def test_continuous_genes_have_valid_ranges():
    for spec in TABLE_GENE_CATALOG:
        if spec.gene_type == GeneType.CONTINUOUS:
            assert spec.min_val < spec.max_val, f"{spec.name}: min >= max"


def test_integer_genes_have_valid_ranges():
    for spec in TABLE_GENE_CATALOG:
        if spec.gene_type == GeneType.INTEGER:
            assert spec.min_val <= spec.max_val, f"{spec.name}: min > max"
