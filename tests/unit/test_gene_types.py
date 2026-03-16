"""Tests for GeneSpec and gene type infrastructure."""

from core.genome.gene_types import GeneSpec, GeneType


def test_gene_type_enum_values():
    assert GeneType.CONTINUOUS.value == "continuous"
    assert GeneType.CATEGORICAL.value == "categorical"
    assert GeneType.BOOLEAN.value == "boolean"
    assert GeneType.INTEGER.value == "integer"


def test_continuous_gene_spec():
    spec = GeneSpec(
        name="width",
        gene_type=GeneType.CONTINUOUS,
        min_val=100.0,
        max_val=2000.0,
        default=500.0,
        layer=3,
    )
    assert spec.name == "width"
    assert spec.min_val == 100.0
    assert spec.max_val == 2000.0


def test_categorical_gene_spec():
    spec = GeneSpec(
        name="symmetry_mode",
        gene_type=GeneType.CATEGORICAL,
        categories=["bilateral", "radial", "none"],
        default="bilateral",
        layer=1,
    )
    assert spec.categories == ["bilateral", "radial", "none"]


def test_boolean_gene_spec():
    spec = GeneSpec(
        name="perforation_flag",
        gene_type=GeneType.BOOLEAN,
        default=False,
        layer=4,
    )
    assert spec.gene_type == GeneType.BOOLEAN


def test_integer_gene_spec():
    spec = GeneSpec(
        name="support_count",
        gene_type=GeneType.INTEGER,
        min_val=3,
        max_val=8,
        default=4,
        layer=2,
    )
    assert spec.min_val == 3


def test_gene_spec_random_value_continuous():
    import random
    rng = random.Random(42)
    spec = GeneSpec(
        name="width", gene_type=GeneType.CONTINUOUS,
        min_val=100.0, max_val=200.0, default=150.0, layer=3,
    )
    val = spec.random_value(rng)
    assert 100.0 <= val <= 200.0


def test_gene_spec_random_value_categorical():
    import random
    rng = random.Random(42)
    spec = GeneSpec(
        name="sym", gene_type=GeneType.CATEGORICAL,
        categories=["a", "b", "c"], default="a", layer=1,
    )
    val = spec.random_value(rng)
    assert val in ["a", "b", "c"]


def test_gene_spec_random_value_boolean():
    import random
    rng = random.Random(42)
    spec = GeneSpec(
        name="flag", gene_type=GeneType.BOOLEAN,
        default=False, layer=4,
    )
    val = spec.random_value(rng)
    assert isinstance(val, bool)


def test_gene_spec_random_value_integer():
    import random
    rng = random.Random(42)
    spec = GeneSpec(
        name="count", gene_type=GeneType.INTEGER,
        min_val=3, max_val=8, default=4, layer=2,
    )
    val = spec.random_value(rng)
    assert isinstance(val, int)
    assert 3 <= val <= 8


def test_gene_spec_clamp_continuous():
    spec = GeneSpec(
        name="width", gene_type=GeneType.CONTINUOUS,
        min_val=100.0, max_val=200.0, default=150.0, layer=3,
    )
    assert spec.clamp(50.0) == 100.0
    assert spec.clamp(250.0) == 200.0
    assert spec.clamp(150.0) == 150.0


def test_gene_spec_clamp_integer():
    spec = GeneSpec(
        name="count", gene_type=GeneType.INTEGER,
        min_val=3, max_val=8, default=4, layer=2,
    )
    assert spec.clamp(1) == 3
    assert spec.clamp(10) == 8
