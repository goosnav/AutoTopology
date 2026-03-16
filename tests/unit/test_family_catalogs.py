"""Tests for lamp, chair catalogs and catalog registry."""

import random

from core.genome.genome import Genome
from core.genome.gene_types import GeneType
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.chair_genes import CHAIR_GENE_CATALOG
from core.genome.catalog_registry import get_catalog


def test_lamp_catalog_has_all_layers():
    layers = {s.layer for s in LAMP_GENE_CATALOG}
    assert layers == {1, 2, 3, 4}


def test_lamp_has_family_specific_genes():
    names = [s.name for s in LAMP_GENE_CATALOG]
    assert "stem_height" in names
    assert "head_diameter" in names
    assert "shade_type" in names


def test_lamp_random_genome_valid():
    genome = Genome.random_init(LAMP_GENE_CATALOG, random.Random(42))
    assert genome.validate(LAMP_GENE_CATALOG)


def test_chair_catalog_has_all_layers():
    layers = {s.layer for s in CHAIR_GENE_CATALOG}
    assert layers == {1, 2, 3, 4}


def test_chair_has_family_specific_genes():
    names = [s.name for s in CHAIR_GENE_CATALOG]
    assert "seat_height" in names
    assert "back_height" in names
    assert "back_angle" in names
    assert "back_present" in names
    assert "arm_present" in names


def test_chair_random_genome_valid():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    assert genome.validate(CHAIR_GENE_CATALOG)


def test_registry_returns_correct_catalog():
    table_cat = get_catalog("table_family")
    lamp_cat = get_catalog("lamp_family")
    chair_cat = get_catalog("chair_family_lite")
    assert table_cat[0].name == "family_name"
    assert any(s.name == "stem_height" for s in lamp_cat)
    assert any(s.name == "seat_height" for s in chair_cat)


def test_registry_unknown_family():
    import pytest
    with pytest.raises(ValueError, match="Unknown family"):
        get_catalog("unknown_family")


def test_all_catalogs_have_defaults():
    for catalog in [LAMP_GENE_CATALOG, CHAIR_GENE_CATALOG]:
        for spec in catalog:
            assert spec.default is not None, f"{spec.name} missing default"
