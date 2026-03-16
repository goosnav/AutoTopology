"""Tests for Genome class."""

import random

from core.genome.gene_types import GeneSpec, GeneType
from core.genome.genome import Genome


SAMPLE_CATALOG = [
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["table_family"], default="table_family"),
    GeneSpec("support_count", GeneType.INTEGER, layer=2,
             min_val=3, max_val=8, default=4),
    GeneSpec("width", GeneType.CONTINUOUS, layer=3,
             min_val=100.0, max_val=2000.0, default=500.0),
    GeneSpec("perforation_flag", GeneType.BOOLEAN, layer=4,
             default=False),
]


def test_genome_random_init():
    rng = random.Random(42)
    genome = Genome.random_init(SAMPLE_CATALOG, rng)
    assert "family_name" in genome.genes
    assert "support_count" in genome.genes
    assert "width" in genome.genes
    assert isinstance(genome.genes["perforation_flag"], bool)


def test_genome_deterministic_with_seed():
    g1 = Genome.random_init(SAMPLE_CATALOG, random.Random(42))
    g2 = Genome.random_init(SAMPLE_CATALOG, random.Random(42))
    assert g1.genes == g2.genes


def test_genome_validate_valid():
    genome = Genome.random_init(SAMPLE_CATALOG, random.Random(42))
    assert genome.validate(SAMPLE_CATALOG) is True


def test_genome_validate_out_of_range():
    genome = Genome.random_init(SAMPLE_CATALOG, random.Random(42))
    genome.genes["width"] = 99999.0
    assert genome.validate(SAMPLE_CATALOG) is False


def test_genome_to_dict_from_dict():
    genome = Genome.random_init(SAMPLE_CATALOG, random.Random(42))
    data = genome.to_dict()
    restored = Genome.from_dict(data)
    assert restored.genes == genome.genes
    assert restored.genome_id == genome.genome_id


def test_genome_has_unique_id():
    g1 = Genome.random_init(SAMPLE_CATALOG, random.Random(1))
    g2 = Genome.random_init(SAMPLE_CATALOG, random.Random(2))
    assert g1.genome_id != g2.genome_id


def test_genome_get_layer():
    genome = Genome.random_init(SAMPLE_CATALOG, random.Random(42))
    layer1 = genome.get_layer(1, SAMPLE_CATALOG)
    assert "family_name" in layer1
    assert "width" not in layer1


def test_genome_clamp_repairs_values():
    genome = Genome.random_init(SAMPLE_CATALOG, random.Random(42))
    genome.genes["width"] = -100.0
    genome.genes["support_count"] = 100
    genome.clamp(SAMPLE_CATALOG)
    assert genome.genes["width"] == 100.0
    assert genome.genes["support_count"] == 8
