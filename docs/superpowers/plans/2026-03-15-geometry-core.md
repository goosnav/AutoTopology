# Phase 2: Geometry Core — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `dev_cli.py generate-candidate-once --family table --seed 42` produces a valid STL file from an evolutionary genome.

**Architecture:** A 4-layer genome (family/archetype, structural graph, continuous shape, optional surface) is decoded into a networkx.Graph with typed nodes and edges, which is then realized as trimesh primitives (box, cylinder, frustum, panel), assembled into a single mesh, validated, optionally repaired, and exported as STL. Each family (table, lamp, chair) has its own gene catalog and mesh generator but shares the common genome, primitive, assembly, and validation infrastructure.

**Tech Stack:** Python 3.11+, trimesh, networkx, numpy, pydantic, pytest, hypothesis

---

## Chunk 1: Gene Infrastructure

### Task 1: GeneSpec dataclass

**Files:**
- Create: `core/genome/gene_types.py`
- Test: `tests/unit/test_gene_types.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_gene_types.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_gene_types.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.genome.gene_types'`

- [ ] **Step 3: Write minimal implementation**

```python
# core/genome/gene_types.py
"""Gene specification types for the genome encoding system."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GeneType(Enum):
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    INTEGER = "integer"


@dataclass(frozen=True)
class GeneSpec:
    """Specification for a single gene in the genome.

    Defines type, valid range/categories, default value, and which
    genome layer it belongs to (1=family, 2=structure, 3=shape, 4=surface).
    """

    name: str
    gene_type: GeneType
    layer: int
    default: Any = None
    min_val: float | int | None = None
    max_val: float | int | None = None
    categories: list[str] = field(default_factory=list)

    def random_value(self, rng: random.Random) -> Any:
        """Generate a random valid value for this gene."""
        if self.gene_type == GeneType.CONTINUOUS:
            return rng.uniform(self.min_val, self.max_val)
        elif self.gene_type == GeneType.INTEGER:
            return rng.randint(int(self.min_val), int(self.max_val))
        elif self.gene_type == GeneType.CATEGORICAL:
            return rng.choice(self.categories)
        elif self.gene_type == GeneType.BOOLEAN:
            return rng.choice([True, False])
        raise ValueError(f"Unknown gene type: {self.gene_type}")

    def clamp(self, value: Any) -> Any:
        """Clamp a value to the valid range for this gene."""
        if self.gene_type in (GeneType.CONTINUOUS, GeneType.INTEGER):
            clamped = max(self.min_val, min(self.max_val, value))
            if self.gene_type == GeneType.INTEGER:
                return int(clamped)
            return clamped
        return value
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_gene_types.py -v`
Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/genome/gene_types.py tests/unit/test_gene_types.py
git commit -m "feat: add GeneSpec dataclass with type-aware random and clamp"
```

---

### Task 2: Genome class

**Files:**
- Create: `core/genome/genome.py`
- Test: `tests/unit/test_genome.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_genome.py
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
    genome.genes["width"] = 99999.0  # way out of range
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_genome.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# core/genome/genome.py
"""Genome class — the genotype for evolutionary candidates."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Any

from core.genome.gene_types import GeneSpec, GeneType


@dataclass
class Genome:
    """A flat-dict genome with typed gene values."""

    genes: dict[str, Any] = field(default_factory=dict)
    genome_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @classmethod
    def random_init(cls, catalog: list[GeneSpec], rng: random.Random) -> Genome:
        """Create a genome with random values from a gene catalog."""
        genes = {spec.name: spec.random_value(rng) for spec in catalog}
        return cls(genes=genes)

    def validate(self, catalog: list[GeneSpec]) -> bool:
        """Check all gene values are within their valid ranges."""
        catalog_map = {s.name: s for s in catalog}
        for name, value in self.genes.items():
            spec = catalog_map.get(name)
            if spec is None:
                return False
            if spec.gene_type == GeneType.CONTINUOUS:
                if not (spec.min_val <= value <= spec.max_val):
                    return False
            elif spec.gene_type == GeneType.INTEGER:
                if not (spec.min_val <= value <= spec.max_val):
                    return False
            elif spec.gene_type == GeneType.CATEGORICAL:
                if value not in spec.categories:
                    return False
        return True

    def get_layer(self, layer: int, catalog: list[GeneSpec]) -> dict[str, Any]:
        """Return only genes belonging to a specific layer."""
        names = {s.name for s in catalog if s.layer == layer}
        return {k: v for k, v in self.genes.items() if k in names}

    def clamp(self, catalog: list[GeneSpec]) -> None:
        """Clamp all gene values to their valid ranges in-place."""
        catalog_map = {s.name: s for s in catalog}
        for name in self.genes:
            spec = catalog_map.get(name)
            if spec:
                self.genes[name] = spec.clamp(self.genes[name])

    def to_dict(self) -> dict:
        """Serialize genome to a plain dict."""
        return {"genome_id": self.genome_id, "genes": dict(self.genes)}

    @classmethod
    def from_dict(cls, data: dict) -> Genome:
        """Deserialize genome from a plain dict."""
        return cls(genes=dict(data["genes"]), genome_id=data["genome_id"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_genome.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/genome/genome.py tests/unit/test_genome.py
git commit -m "feat: add Genome class with random init, validation, serialization"
```

---

### Task 3: Table family gene catalog

**Files:**
- Create: `core/genome/table_genes.py`
- Test: `tests/unit/test_table_genes.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_table_genes.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_table_genes.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# core/genome/table_genes.py
"""Gene catalog for the table family."""

from core.genome.gene_types import GeneSpec, GeneType

TABLE_GENE_CATALOG: list[GeneSpec] = [
    # --- Layer 1: Family / Archetype ---
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["table_family"], default="table_family"),
    GeneSpec("subtype", GeneType.CATEGORICAL, layer=1,
             categories=["dining", "coffee", "side", "console", "desk"],
             default="dining"),
    GeneSpec("topology_family", GeneType.CATEGORICAL, layer=1,
             categories=["skeletal", "monolithic", "hybrid"],
             default="skeletal"),
    GeneSpec("symmetry_mode", GeneType.CATEGORICAL, layer=1,
             categories=["bilateral", "radial", "none"],
             default="bilateral"),
    GeneSpec("support_strategy", GeneType.CATEGORICAL, layer=1,
             categories=["corner", "pedestal", "trestle", "cantilever"],
             default="corner"),
    GeneSpec("decorative_bias", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.3),
    GeneSpec("monolithic_ratio", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.0),

    # --- Layer 2: Structural Graph ---
    GeneSpec("support_count", GeneType.INTEGER, layer=2,
             min_val=1, max_val=8, default=4),
    GeneSpec("branch_depth", GeneType.INTEGER, layer=2,
             min_val=0, max_val=3, default=0),
    GeneSpec("brace_count", GeneType.INTEGER, layer=2,
             min_val=0, max_val=6, default=0),
    GeneSpec("connectivity_density", GeneType.CONTINUOUS, layer=2,
             min_val=0.0, max_val=1.0, default=0.3),

    # --- Layer 3: Continuous Shape ---
    GeneSpec("width", GeneType.CONTINUOUS, layer=3,
             min_val=200.0, max_val=2000.0, default=800.0),
    GeneSpec("depth", GeneType.CONTINUOUS, layer=3,
             min_val=200.0, max_val=1500.0, default=600.0),
    GeneSpec("height", GeneType.CONTINUOUS, layer=3,
             min_val=200.0, max_val=1200.0, default=750.0),
    GeneSpec("top_thickness", GeneType.CONTINUOUS, layer=3,
             min_val=5.0, max_val=80.0, default=25.0),
    GeneSpec("member_thickness", GeneType.CONTINUOUS, layer=3,
             min_val=8.0, max_val=120.0, default=40.0),
    GeneSpec("support_angle", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=30.0, default=0.0),
    GeneSpec("taper_ratio", GeneType.CONTINUOUS, layer=3,
             min_val=0.5, max_val=1.5, default=1.0),
    GeneSpec("curve_bias", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("footprint_inset", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=0.4, default=0.05),
    GeneSpec("fillet_radius", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=20.0, default=2.0),

    # --- Layer 4: Optional Surface ---
    GeneSpec("perforation_flag", GeneType.BOOLEAN, layer=4, default=False),
    GeneSpec("perforation_density", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("cutout_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("ribbing_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("asymmetry_offset_x", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
    GeneSpec("asymmetry_offset_y", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_table_genes.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/genome/table_genes.py tests/unit/test_table_genes.py
git commit -m "feat: add table family gene catalog (4 layers, 26 genes)"
```

---

### Task 4: Lamp and chair gene catalogs

**Files:**
- Create: `core/genome/lamp_genes.py`
- Create: `core/genome/chair_genes.py`
- Create: `core/genome/catalog_registry.py`
- Test: `tests/unit/test_family_catalogs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_family_catalogs.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_family_catalogs.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write lamp catalog**

```python
# core/genome/lamp_genes.py
"""Gene catalog for the lamp family."""

from core.genome.gene_types import GeneSpec, GeneType

LAMP_GENE_CATALOG: list[GeneSpec] = [
    # --- Layer 1: Family / Archetype ---
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["lamp_family"], default="lamp_family"),
    GeneSpec("subtype", GeneType.CATEGORICAL, layer=1,
             categories=["desk", "floor", "pendant", "wall"],
             default="desk"),
    GeneSpec("topology_family", GeneType.CATEGORICAL, layer=1,
             categories=["skeletal", "monolithic", "hybrid"],
             default="skeletal"),
    GeneSpec("symmetry_mode", GeneType.CATEGORICAL, layer=1,
             categories=["bilateral", "radial", "none"],
             default="radial"),
    GeneSpec("support_strategy", GeneType.CATEGORICAL, layer=1,
             categories=["base_plate", "tripod", "clamp", "weighted"],
             default="base_plate"),
    GeneSpec("decorative_bias", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.5),
    GeneSpec("monolithic_ratio", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.0),

    # --- Layer 2: Structural Graph ---
    GeneSpec("support_count", GeneType.INTEGER, layer=2,
             min_val=1, max_val=5, default=1),
    GeneSpec("branch_depth", GeneType.INTEGER, layer=2,
             min_val=0, max_val=3, default=0),
    GeneSpec("brace_count", GeneType.INTEGER, layer=2,
             min_val=0, max_val=4, default=0),
    GeneSpec("shade_type", GeneType.CATEGORICAL, layer=2,
             categories=["cone", "dome", "cylinder", "flat", "none"],
             default="cone"),
    GeneSpec("connectivity_density", GeneType.CONTINUOUS, layer=2,
             min_val=0.0, max_val=1.0, default=0.2),

    # --- Layer 3: Continuous Shape ---
    GeneSpec("width", GeneType.CONTINUOUS, layer=3,
             min_val=50.0, max_val=600.0, default=200.0),
    GeneSpec("depth", GeneType.CONTINUOUS, layer=3,
             min_val=50.0, max_val=600.0, default=200.0),
    GeneSpec("height", GeneType.CONTINUOUS, layer=3,
             min_val=150.0, max_val=1800.0, default=450.0),
    GeneSpec("stem_height", GeneType.CONTINUOUS, layer=3,
             min_val=50.0, max_val=1500.0, default=300.0),
    GeneSpec("head_diameter", GeneType.CONTINUOUS, layer=3,
             min_val=30.0, max_val=500.0, default=150.0),
    GeneSpec("member_thickness", GeneType.CONTINUOUS, layer=3,
             min_val=5.0, max_val=60.0, default=15.0),
    GeneSpec("taper_ratio", GeneType.CONTINUOUS, layer=3,
             min_val=0.3, max_val=2.0, default=1.0),
    GeneSpec("curve_bias", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=1.0, default=0.2),
    GeneSpec("fillet_radius", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=15.0, default=2.0),

    # --- Layer 4: Optional Surface ---
    GeneSpec("perforation_flag", GeneType.BOOLEAN, layer=4, default=False),
    GeneSpec("perforation_density", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("cutout_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("ribbing_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("asymmetry_offset_x", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
    GeneSpec("asymmetry_offset_y", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
]
```

- [ ] **Step 4: Write chair catalog**

```python
# core/genome/chair_genes.py
"""Gene catalog for the chair family (lite)."""

from core.genome.gene_types import GeneSpec, GeneType

CHAIR_GENE_CATALOG: list[GeneSpec] = [
    # --- Layer 1: Family / Archetype ---
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["chair_family_lite"], default="chair_family_lite"),
    GeneSpec("subtype", GeneType.CATEGORICAL, layer=1,
             categories=["dining", "lounge", "stool", "office"],
             default="dining"),
    GeneSpec("topology_family", GeneType.CATEGORICAL, layer=1,
             categories=["skeletal", "monolithic", "hybrid"],
             default="skeletal"),
    GeneSpec("symmetry_mode", GeneType.CATEGORICAL, layer=1,
             categories=["bilateral", "none"],
             default="bilateral"),
    GeneSpec("support_strategy", GeneType.CATEGORICAL, layer=1,
             categories=["four_leg", "sled", "cantilever", "pedestal"],
             default="four_leg"),
    GeneSpec("decorative_bias", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.3),
    GeneSpec("monolithic_ratio", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.0),

    # --- Layer 2: Structural Graph ---
    GeneSpec("support_count", GeneType.INTEGER, layer=2,
             min_val=1, max_val=6, default=4),
    GeneSpec("branch_depth", GeneType.INTEGER, layer=2,
             min_val=0, max_val=2, default=0),
    GeneSpec("brace_count", GeneType.INTEGER, layer=2,
             min_val=0, max_val=6, default=0),
    GeneSpec("back_present", GeneType.BOOLEAN, layer=2, default=True),
    GeneSpec("arm_present", GeneType.BOOLEAN, layer=2, default=False),
    GeneSpec("connectivity_density", GeneType.CONTINUOUS, layer=2,
             min_val=0.0, max_val=1.0, default=0.3),

    # --- Layer 3: Continuous Shape ---
    GeneSpec("width", GeneType.CONTINUOUS, layer=3,
             min_val=300.0, max_val=800.0, default=450.0),
    GeneSpec("depth", GeneType.CONTINUOUS, layer=3,
             min_val=300.0, max_val=700.0, default=450.0),
    GeneSpec("height", GeneType.CONTINUOUS, layer=3,
             min_val=600.0, max_val=1200.0, default=850.0),
    GeneSpec("seat_height", GeneType.CONTINUOUS, layer=3,
             min_val=350.0, max_val=550.0, default=450.0),
    GeneSpec("back_height", GeneType.CONTINUOUS, layer=3,
             min_val=150.0, max_val=700.0, default=400.0),
    GeneSpec("back_angle", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=30.0, default=5.0),
    GeneSpec("member_thickness", GeneType.CONTINUOUS, layer=3,
             min_val=10.0, max_val=80.0, default=30.0),
    GeneSpec("taper_ratio", GeneType.CONTINUOUS, layer=3,
             min_val=0.5, max_val=1.5, default=1.0),
    GeneSpec("curve_bias", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("fillet_radius", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=15.0, default=2.0),

    # --- Layer 4: Optional Surface ---
    GeneSpec("perforation_flag", GeneType.BOOLEAN, layer=4, default=False),
    GeneSpec("perforation_density", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("cutout_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("ribbing_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("asymmetry_offset_x", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
    GeneSpec("asymmetry_offset_y", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
]
```

- [ ] **Step 5: Write catalog registry**

```python
# core/genome/catalog_registry.py
"""Registry mapping family names to their gene catalogs."""

from core.genome.gene_types import GeneSpec
from core.genome.table_genes import TABLE_GENE_CATALOG
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.chair_genes import CHAIR_GENE_CATALOG

_CATALOGS: dict[str, list[GeneSpec]] = {
    "table_family": TABLE_GENE_CATALOG,
    "lamp_family": LAMP_GENE_CATALOG,
    "chair_family_lite": CHAIR_GENE_CATALOG,
}


def get_catalog(family_name: str) -> list[GeneSpec]:
    """Return the gene catalog for a given family name."""
    if family_name not in _CATALOGS:
        raise ValueError(f"Unknown family: {family_name}. Available: {list(_CATALOGS.keys())}")
    return _CATALOGS[family_name]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_family_catalogs.py -v`
Expected: All 10 tests PASS

- [ ] **Step 7: Commit**

```bash
git add core/genome/lamp_genes.py core/genome/chair_genes.py core/genome/catalog_registry.py tests/unit/test_family_catalogs.py
git commit -m "feat: add lamp/chair gene catalogs and family registry"
```

---

## Chunk 2: Graph Builder & Primitives

### Task 5: Graph builder (Genome -> networkx.Graph)

**Files:**
- Create: `core/genome/graph_builder.py`
- Test: `tests/unit/test_graph_builder.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_graph_builder.py
"""Tests for genome-to-graph builder."""

import random

import networkx as nx

from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.chair_genes import CHAIR_GENE_CATALOG
from core.genome.graph_builder import build_graph


def test_table_graph_has_surface_node():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    surface_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "surface"]
    assert len(surface_nodes) >= 1


def test_table_graph_has_support_nodes():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    support_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "ground_anchor"]
    assert len(support_nodes) >= 1


def test_table_graph_is_connected():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    assert nx.is_connected(G)


def test_table_graph_edges_have_types():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    for u, v, d in G.edges(data=True):
        assert "edge_type" in d


def test_lamp_graph_has_head_node():
    genome = Genome.random_init(LAMP_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, LAMP_GENE_CATALOG)
    head_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "head"]
    assert len(head_nodes) >= 1


def test_chair_graph_has_seat():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, CHAIR_GENE_CATALOG)
    seat_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "surface"]
    assert len(seat_nodes) >= 1


def test_graph_deterministic():
    g1 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    g2 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G1 = build_graph(g1, TABLE_GENE_CATALOG)
    G2 = build_graph(g2, TABLE_GENE_CATALOG)
    assert list(G1.nodes) == list(G2.nodes)
    assert list(G1.edges) == list(G2.edges)


def test_graph_nodes_have_positions():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    for n, d in G.nodes(data=True):
        assert "pos" in d, f"Node {n} missing 'pos'"
        assert len(d["pos"]) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_graph_builder.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# core/genome/graph_builder.py
"""Build a structural graph from a genome.

Each family produces a networkx.Graph with typed nodes (surface, ground_anchor,
head, etc.) and typed edges (support_member, brace_member, etc.). Node positions
are 3D coordinates in mm.
"""

from __future__ import annotations

import math

import networkx as nx
import numpy as np

from core.genome.gene_types import GeneSpec
from core.genome.genome import Genome


def build_graph(genome: Genome, catalog: list[GeneSpec]) -> nx.Graph:
    """Dispatch to family-specific graph builder."""
    family = genome.genes.get("family_name")
    if family == "table_family":
        return _build_table_graph(genome)
    elif family == "lamp_family":
        return _build_lamp_graph(genome)
    elif family == "chair_family_lite":
        return _build_chair_graph(genome)
    raise ValueError(f"Unknown family: {family}")


def _build_table_graph(genome: Genome) -> nx.Graph:
    g = genome.genes
    G = nx.Graph()

    w, d, h = g["width"], g["depth"], g["height"]
    top_t = g["top_thickness"]
    n_supports = g["support_count"]
    inset = g["footprint_inset"]

    # Surface node (table top center)
    G.add_node("top", node_type="surface", pos=(0.0, 0.0, h))

    # Place supports based on strategy
    strategy = g["support_strategy"]
    support_positions = _place_supports(strategy, n_supports, w, d, inset)

    for i, (sx, sy) in enumerate(support_positions):
        node_id = f"leg_{i}"
        G.add_node(node_id, node_type="ground_anchor", pos=(sx, sy, 0.0))
        # Surface anchor point where leg meets top
        anchor_id = f"leg_top_{i}"
        G.add_node(anchor_id, node_type="surface_anchor", pos=(sx, sy, h - top_t))
        G.add_edge("top", anchor_id, edge_type="panel_attachment")
        G.add_edge(anchor_id, node_id, edge_type="support_member")

    # Braces between adjacent supports
    n_braces = min(g["brace_count"], len(support_positions))
    for i in range(n_braces):
        j = (i + 1) % len(support_positions)
        src = f"leg_{i}"
        dst = f"leg_{j}"
        brace_h = h * 0.3
        brace_id = f"brace_{i}"
        sx, sy, _ = G.nodes[src]["pos"]
        dx, dy, _ = G.nodes[dst]["pos"]
        mx, my = (sx + dx) / 2, (sy + dy) / 2
        G.add_node(brace_id, node_type="brace_point", pos=(mx, my, brace_h))
        G.add_edge(src, brace_id, edge_type="brace_member")
        G.add_edge(dst, brace_id, edge_type="brace_member")

    return G


def _build_lamp_graph(genome: Genome) -> nx.Graph:
    g = genome.genes
    G = nx.Graph()

    h = g["height"]
    stem_h = min(g["stem_height"], h * 0.9)
    head_d = g["head_diameter"]
    n_supports = g["support_count"]
    w, d = g["width"], g["depth"]

    # Base
    G.add_node("base", node_type="ground_anchor", pos=(0.0, 0.0, 0.0))

    # Stem top
    G.add_node("stem_top", node_type="junction", pos=(0.0, 0.0, stem_h))
    G.add_edge("base", "stem_top", edge_type="support_member")

    # Head
    G.add_node("head", node_type="head", pos=(0.0, 0.0, h))
    G.add_edge("stem_top", "head", edge_type="support_member")

    # Additional support legs for tripod etc
    if n_supports > 1:
        angle_step = 2 * math.pi / n_supports
        base_r = w * 0.3
        for i in range(n_supports):
            angle = i * angle_step
            x = base_r * math.cos(angle)
            y = base_r * math.sin(angle)
            leg_id = f"foot_{i}"
            G.add_node(leg_id, node_type="ground_anchor", pos=(x, y, 0.0))
            G.add_edge(leg_id, "base", edge_type="brace_member")

    return G


def _build_chair_graph(genome: Genome) -> nx.Graph:
    g = genome.genes
    G = nx.Graph()

    w, d = g["width"], g["depth"]
    seat_h = g["seat_height"]
    n_supports = g["support_count"]
    has_back = g["back_present"]
    has_arms = g["arm_present"]
    back_h = g["back_height"]
    back_angle_deg = g["back_angle"]

    # Seat surface
    G.add_node("seat", node_type="surface", pos=(0.0, 0.0, seat_h))

    # Legs
    support_positions = _place_supports("corner", min(n_supports, 4), w, d, 0.05)
    for i, (sx, sy) in enumerate(support_positions):
        leg_id = f"leg_{i}"
        G.add_node(leg_id, node_type="ground_anchor", pos=(sx, sy, 0.0))
        anchor_id = f"leg_top_{i}"
        G.add_node(anchor_id, node_type="surface_anchor", pos=(sx, sy, seat_h))
        G.add_edge("seat", anchor_id, edge_type="panel_attachment")
        G.add_edge(anchor_id, leg_id, edge_type="support_member")

    # Back
    if has_back:
        back_angle_rad = math.radians(back_angle_deg)
        back_top_y = -d / 2 - back_h * math.sin(back_angle_rad)
        back_top_z = seat_h + back_h * math.cos(back_angle_rad)
        G.add_node("back_top", node_type="back",
                    pos=(0.0, back_top_y, back_top_z))
        G.add_node("back_base", node_type="back_anchor",
                    pos=(0.0, -d / 2, seat_h))
        G.add_edge("seat", "back_base", edge_type="panel_attachment")
        G.add_edge("back_base", "back_top", edge_type="support_member")

    # Arms
    if has_arms:
        arm_h = seat_h + back_h * 0.5
        for side, x_sign in [("left", -1), ("right", 1)]:
            arm_id = f"arm_{side}"
            G.add_node(arm_id, node_type="arm",
                        pos=(x_sign * w / 2, 0.0, arm_h))
            G.add_edge("seat", arm_id, edge_type="panel_attachment")

    # Braces
    n_braces = min(g["brace_count"], len(support_positions))
    for i in range(n_braces):
        j = (i + 1) % len(support_positions)
        brace_id = f"brace_{i}"
        s_pos = G.nodes[f"leg_{i}"]["pos"]
        d_pos = G.nodes[f"leg_{j}"]["pos"]
        mx = (s_pos[0] + d_pos[0]) / 2
        my = (s_pos[1] + d_pos[1]) / 2
        G.add_node(brace_id, node_type="brace_point",
                    pos=(mx, my, seat_h * 0.3))
        G.add_edge(f"leg_{i}", brace_id, edge_type="brace_member")
        G.add_edge(f"leg_{j}", brace_id, edge_type="brace_member")

    return G


def _place_supports(
    strategy: str, count: int, width: float, depth: float, inset: float,
) -> list[tuple[float, float]]:
    """Compute 2D support positions based on strategy."""
    count = max(1, count)
    hw = width / 2 * (1 - inset)
    hd = depth / 2 * (1 - inset)

    if strategy == "pedestal" or count == 1:
        return [(0.0, 0.0)]

    if strategy in ("corner", "four_leg") and count >= 4:
        return [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)][:count]

    if strategy == "trestle" and count >= 2:
        return [(-hw, 0.0), (hw, 0.0)]

    # Radial fallback
    positions = []
    for i in range(count):
        angle = 2 * math.pi * i / count
        x = hw * math.cos(angle)
        y = hd * math.sin(angle)
        positions.append((x, y))
    return positions
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_graph_builder.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/genome/graph_builder.py tests/unit/test_graph_builder.py
git commit -m "feat: add graph builder for table, lamp, chair families"
```

---

### Task 6: Primitive mesh factories

**Files:**
- Create: `geometry/primitives/primitives.py`
- Test: `tests/unit/test_primitives.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_primitives.py
"""Tests for primitive mesh factories."""

import numpy as np
import trimesh

from geometry.primitives.primitives import make_box, make_cylinder, make_frustum, make_panel


def test_make_box_dimensions():
    mesh = make_box(100, 200, 50)
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents, [100, 200, 50], atol=0.1)


def test_make_box_is_watertight():
    mesh = make_box(100, 200, 50)
    assert mesh.is_watertight


def test_make_box_with_position():
    mesh = make_box(100, 100, 100, center=(50, 50, 50))
    centroid = mesh.centroid
    np.testing.assert_allclose(centroid, [50, 50, 50], atol=0.1)


def test_make_cylinder_is_watertight():
    mesh = make_cylinder(radius=20, height=100)
    assert mesh.is_watertight


def test_make_cylinder_dimensions():
    mesh = make_cylinder(radius=25, height=200)
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents[2], 200, atol=1.0)
    np.testing.assert_allclose(extents[0], 50, atol=2.0)


def test_make_frustum_is_watertight():
    mesh = make_frustum(r_bottom=30, r_top=20, height=100)
    assert mesh.is_watertight


def test_make_frustum_with_taper():
    mesh = make_frustum(r_bottom=40, r_top=10, height=150)
    assert mesh.is_watertight
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents[2], 150, atol=1.0)


def test_make_panel_is_watertight():
    mesh = make_panel(width=200, height=300, thickness=10)
    assert mesh.is_watertight


def test_make_panel_dimensions():
    mesh = make_panel(width=200, height=300, thickness=10)
    extents = mesh.bounding_box.extents
    np.testing.assert_allclose(extents, [200, 10, 300], atol=0.1)


def test_make_cylinder_with_position():
    mesh = make_cylinder(radius=20, height=100, center=(100, 200, 50))
    centroid = mesh.centroid
    np.testing.assert_allclose(centroid, [100, 200, 50], atol=1.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_primitives.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# geometry/primitives/primitives.py
"""Primitive mesh factories.

Each factory returns a watertight trimesh.Trimesh positioned at the
specified center. All dimensions are in mm.
"""

from __future__ import annotations

import numpy as np
import trimesh


def make_box(
    width: float, depth: float, height: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> trimesh.Trimesh:
    """Create a box (rectangular prism) centered at `center`."""
    mesh = trimesh.creation.box(extents=(width, depth, height))
    mesh.apply_translation(center)
    return mesh


def make_cylinder(
    radius: float, height: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    sections: int = 24,
) -> trimesh.Trimesh:
    """Create a cylinder centered at `center`, axis along Z."""
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation(center)
    return mesh


def make_frustum(
    r_bottom: float, r_top: float, height: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    sections: int = 24,
) -> trimesh.Trimesh:
    """Create a frustum (tapered cylinder) centered at `center`."""
    # Build as a cylinder section-by-section using revolution
    angles = np.linspace(0, 2 * np.pi, sections + 1)
    # Two rings of vertices
    bottom_ring = np.column_stack([
        r_bottom * np.cos(angles[:-1]),
        r_bottom * np.sin(angles[:-1]),
        np.full(sections, -height / 2),
    ])
    top_ring = np.column_stack([
        r_top * np.cos(angles[:-1]),
        r_top * np.sin(angles[:-1]),
        np.full(sections, height / 2),
    ])

    vertices = np.vstack([bottom_ring, top_ring])
    n = sections
    faces = []

    # Side faces (quads as triangle pairs)
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j])
        faces.append([i, n + j, n + i])

    # Bottom cap (fan from center)
    bottom_center_idx = len(vertices)
    vertices = np.vstack([vertices, [[0, 0, -height / 2]]])
    for i in range(n):
        j = (i + 1) % n
        faces.append([bottom_center_idx, j, i])

    # Top cap (fan from center)
    top_center_idx = len(vertices)
    vertices = np.vstack([vertices, [[0, 0, height / 2]]])
    for i in range(n):
        j = (i + 1) % n
        faces.append([top_center_idx, n + i, n + j])

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces))
    mesh.fix_normals()
    mesh.apply_translation(center)
    return mesh


def make_panel(
    width: float, height: float, thickness: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> trimesh.Trimesh:
    """Create a thin panel (width x thickness x height), upright along Z."""
    return make_box(width, thickness, height, center=center)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_primitives.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add geometry/primitives/primitives.py tests/unit/test_primitives.py
git commit -m "feat: add primitive mesh factories (box, cylinder, frustum, panel)"
```

---

## Chunk 3: Mesh Generation Pipeline

### Task 7: Mesh assembler

**Files:**
- Create: `geometry/composition/assembler.py`
- Test: `tests/unit/test_assembler.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_assembler.py
"""Tests for mesh assembler."""

import trimesh

from geometry.composition.assembler import assemble_meshes
from geometry.primitives.primitives import make_box, make_cylinder


def test_assemble_two_boxes():
    a = make_box(100, 100, 100, center=(0, 0, 50))
    b = make_box(20, 20, 200, center=(0, 0, 100))
    combined = assemble_meshes([a, b])
    assert isinstance(combined, trimesh.Trimesh)
    assert len(combined.vertices) == len(a.vertices) + len(b.vertices)


def test_assemble_single_mesh():
    a = make_box(100, 100, 100)
    combined = assemble_meshes([a])
    assert len(combined.vertices) == len(a.vertices)


def test_assemble_empty_list():
    import pytest
    with pytest.raises(ValueError, match="No meshes"):
        assemble_meshes([])


def test_assemble_preserves_faces():
    a = make_box(50, 50, 50)
    b = make_cylinder(10, 100)
    combined = assemble_meshes([a, b])
    assert len(combined.faces) == len(a.faces) + len(b.faces)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_assembler.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# geometry/composition/assembler.py
"""Assemble multiple trimesh primitives into a single mesh."""

from __future__ import annotations

import trimesh


def assemble_meshes(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    """Concatenate meshes into a single combined mesh.

    Uses trimesh concatenation (vertex array stacking) rather than
    boolean operations to preserve watertightness of individual parts.
    """
    if not meshes:
        raise ValueError("No meshes to assemble")
    if len(meshes) == 1:
        return meshes[0].copy()
    return trimesh.util.concatenate(meshes)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_assembler.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add geometry/composition/assembler.py tests/unit/test_assembler.py
git commit -m "feat: add mesh assembler using trimesh concatenation"
```

---

### Task 8: Table mesh generator

**Files:**
- Create: `geometry/generators/table_generator.py`
- Test: `tests/unit/test_table_generator.py`

- [ ] **Step 1: Write the failing test**

```python
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
    # Different seeds should produce different vertex counts or positions
    assert not (m1.vertices == m2.vertices).all() or len(m1.vertices) != len(m2.vertices)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_table_generator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# geometry/generators/table_generator.py
"""Generate table meshes from genomes."""

from __future__ import annotations

import math

import numpy as np
import trimesh

from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from core.genome.graph_builder import build_graph
from geometry.primitives.primitives import make_box, make_cylinder, make_frustum
from geometry.composition.assembler import assemble_meshes


def generate_table_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a table mesh from a genome."""
    g = genome.genes
    G = build_graph(genome, TABLE_GENE_CATALOG)

    parts: list[trimesh.Trimesh] = []

    w, d, h = g["width"], g["depth"], g["height"]
    top_t = g["top_thickness"]
    member_t = g["member_thickness"]
    taper = g["taper_ratio"]

    # Table top
    top = make_box(w, d, top_t, center=(0, 0, h - top_t / 2))
    parts.append(top)

    # Legs: edges of type "support_member"
    for u, v, data in G.edges(data=True):
        if data["edge_type"] != "support_member":
            continue
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        # Find which is higher (surface_anchor) vs lower (ground_anchor)
        if pos_u[2] > pos_v[2]:
            top_pos, bot_pos = pos_u, pos_v
        else:
            top_pos, bot_pos = pos_v, pos_u

        leg_h = float(np.linalg.norm(top_pos - bot_pos))
        if leg_h < 1.0:
            continue

        center = ((top_pos + bot_pos) / 2).tolist()
        r_bot = member_t / 2
        r_top = r_bot * taper

        leg = make_frustum(r_bot, r_top, leg_h, center=tuple(center))

        # Tilt the leg if not vertical
        direction = top_pos - bot_pos
        direction_norm = direction / np.linalg.norm(direction)
        z_axis = np.array([0, 0, 1])

        if not np.allclose(direction_norm, z_axis, atol=1e-6):
            axis = np.cross(z_axis, direction_norm)
            axis_len = np.linalg.norm(axis)
            if axis_len > 1e-8:
                axis = axis / axis_len
                angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                rot = trimesh.transformations.rotation_matrix(angle, axis, point=center)
                leg.apply_transform(rot)

        parts.append(leg)

    # Braces
    for u, v, data in G.edges(data=True):
        if data["edge_type"] != "brace_member":
            continue
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        brace_len = float(np.linalg.norm(pos_u - pos_v))
        if brace_len < 1.0:
            continue

        center = ((pos_u + pos_v) / 2).tolist()
        brace = make_cylinder(member_t / 4, brace_len, center=tuple(center))

        direction = pos_v - pos_u
        direction_norm = direction / np.linalg.norm(direction)
        z_axis = np.array([0, 0, 1])
        if not np.allclose(direction_norm, z_axis, atol=1e-6):
            axis = np.cross(z_axis, direction_norm)
            axis_len = np.linalg.norm(axis)
            if axis_len > 1e-8:
                axis = axis / axis_len
                angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                rot = trimesh.transformations.rotation_matrix(angle, axis, point=center)
                brace.apply_transform(rot)

        parts.append(brace)

    return assemble_meshes(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_table_generator.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add geometry/generators/table_generator.py tests/unit/test_table_generator.py
git commit -m "feat: add table mesh generator (genome -> graph -> primitives -> mesh)"
```

---

### Task 9: Lamp and chair mesh generators

**Files:**
- Create: `geometry/generators/lamp_generator.py`
- Create: `geometry/generators/chair_generator.py`
- Create: `geometry/generators/generator_registry.py`
- Test: `tests/unit/test_lamp_chair_generators.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_lamp_chair_generators.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write lamp generator**

```python
# geometry/generators/lamp_generator.py
"""Generate lamp meshes from genomes."""

from __future__ import annotations

import math

import numpy as np
import trimesh

from core.genome.genome import Genome
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.graph_builder import build_graph
from geometry.primitives.primitives import make_box, make_cylinder, make_frustum
from geometry.composition.assembler import assemble_meshes


def generate_lamp_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a lamp mesh from a genome."""
    g = genome.genes
    G = build_graph(genome, LAMP_GENE_CATALOG)

    parts: list[trimesh.Trimesh] = []

    member_t = g["member_thickness"]
    head_d = g["head_diameter"]
    shade = g.get("shade_type", "cone")
    taper = g["taper_ratio"]

    # Build parts from graph edges
    for u, v, data in G.edges(data=True):
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        seg_len = float(np.linalg.norm(pos_u - pos_v))
        if seg_len < 1.0:
            continue

        center = tuple(((pos_u + pos_v) / 2).tolist())
        r = member_t / 2

        if data["edge_type"] == "support_member":
            part = make_frustum(r, r * taper, seg_len, center=center)
        else:
            part = make_cylinder(r * 0.6, seg_len, center=center)

        # Orient along edge direction
        direction = pos_v - pos_u
        direction_norm = direction / np.linalg.norm(direction)
        z_axis = np.array([0, 0, 1])
        if not np.allclose(direction_norm, z_axis, atol=1e-6):
            axis = np.cross(z_axis, direction_norm)
            axis_len = np.linalg.norm(axis)
            if axis_len > 1e-8:
                axis = axis / axis_len
                angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                rot = trimesh.transformations.rotation_matrix(angle, axis, point=list(center))
                part.apply_transform(rot)

        parts.append(part)

    # Lamp head/shade
    head_node = G.nodes.get("head")
    if head_node:
        head_pos = head_node["pos"]
        shade_h = head_d * 0.6
        if shade == "cone":
            head_mesh = make_frustum(head_d / 2, head_d / 6, shade_h,
                                     center=(head_pos[0], head_pos[1], head_pos[2] + shade_h / 2))
        elif shade == "dome":
            head_mesh = trimesh.creation.icosphere(radius=head_d / 2)
            head_mesh.apply_translation(head_pos)
        elif shade == "flat":
            head_mesh = make_box(head_d, head_d, shade_h * 0.3,
                                 center=(head_pos[0], head_pos[1], head_pos[2]))
        else:  # cylinder or none
            head_mesh = make_cylinder(head_d / 2, shade_h,
                                      center=(head_pos[0], head_pos[1], head_pos[2] + shade_h / 2))
        parts.append(head_mesh)

    # Base plate
    base_node = G.nodes.get("base")
    if base_node:
        base_pos = base_node["pos"]
        base_r = g["width"] * 0.3
        base_h = member_t * 0.5
        base = make_cylinder(base_r, base_h,
                             center=(base_pos[0], base_pos[1], base_pos[2] + base_h / 2))
        parts.append(base)

    return assemble_meshes(parts)
```

- [ ] **Step 4: Write chair generator**

```python
# geometry/generators/chair_generator.py
"""Generate chair meshes from genomes."""

from __future__ import annotations

import math

import numpy as np
import trimesh

from core.genome.genome import Genome
from core.genome.chair_genes import CHAIR_GENE_CATALOG
from core.genome.graph_builder import build_graph
from geometry.primitives.primitives import make_box, make_cylinder, make_frustum, make_panel
from geometry.composition.assembler import assemble_meshes


def generate_chair_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a chair mesh from a genome."""
    g = genome.genes
    G = build_graph(genome, CHAIR_GENE_CATALOG)

    parts: list[trimesh.Trimesh] = []

    w, d = g["width"], g["depth"]
    seat_h = g["seat_height"]
    member_t = g["member_thickness"]
    taper = g["taper_ratio"]
    seat_thickness = max(member_t * 0.5, 15.0)

    # Seat
    seat = make_box(w, d, seat_thickness,
                    center=(0, 0, seat_h - seat_thickness / 2))
    parts.append(seat)

    # Legs and braces from graph
    for u, v, data in G.edges(data=True):
        if data["edge_type"] not in ("support_member", "brace_member"):
            continue
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        seg_len = float(np.linalg.norm(pos_u - pos_v))
        if seg_len < 1.0:
            continue

        center = tuple(((pos_u + pos_v) / 2).tolist())

        if data["edge_type"] == "support_member":
            r_bot = member_t / 2
            r_top = r_bot * taper
            part = make_frustum(r_bot, r_top, seg_len, center=center)
        else:
            part = make_cylinder(member_t / 4, seg_len, center=center)

        direction = pos_v - pos_u
        direction_norm = direction / np.linalg.norm(direction)
        z_axis = np.array([0, 0, 1])
        if not np.allclose(direction_norm, z_axis, atol=1e-6):
            axis = np.cross(z_axis, direction_norm)
            axis_len = np.linalg.norm(axis)
            if axis_len > 1e-8:
                axis = axis / axis_len
                angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                rot = trimesh.transformations.rotation_matrix(angle, axis, point=list(center))
                part.apply_transform(rot)

        parts.append(part)

    # Back panel
    back_top_node = G.nodes.get("back_top")
    back_base_node = G.nodes.get("back_base")
    if back_top_node and back_base_node:
        back_top_pos = np.array(back_top_node["pos"])
        back_base_pos = np.array(back_base_node["pos"])
        back_h = float(np.linalg.norm(back_top_pos - back_base_pos))
        if back_h > 1.0:
            center = tuple(((back_top_pos + back_base_pos) / 2).tolist())
            back = make_panel(w * 0.9, back_h, seat_thickness * 0.7, center=center)

            # Tilt the back
            direction = back_top_pos - back_base_pos
            direction_norm = direction / np.linalg.norm(direction)
            z_axis = np.array([0, 0, 1])
            if not np.allclose(direction_norm, z_axis, atol=1e-6):
                axis = np.cross(z_axis, direction_norm)
                axis_len = np.linalg.norm(axis)
                if axis_len > 1e-8:
                    axis = axis / axis_len
                    angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                    rot = trimesh.transformations.rotation_matrix(angle, axis, point=list(center))
                    back.apply_transform(rot)

            parts.append(back)

    # Arm rests
    for side in ("left", "right"):
        arm_node = G.nodes.get(f"arm_{side}")
        if arm_node:
            arm_pos = arm_node["pos"]
            arm_len = d * 0.6
            arm = make_box(member_t, arm_len, member_t * 0.5,
                           center=(arm_pos[0], arm_pos[1], arm_pos[2]))
            parts.append(arm)

    return assemble_meshes(parts)
```

- [ ] **Step 5: Write generator registry**

```python
# geometry/generators/generator_registry.py
"""Registry dispatching genome to family-specific mesh generator."""

from __future__ import annotations

import trimesh

from core.genome.genome import Genome


def generate_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a mesh from a genome, dispatching by family."""
    family = genome.genes.get("family_name")
    if family == "table_family":
        from geometry.generators.table_generator import generate_table_mesh
        return generate_table_mesh(genome)
    elif family == "lamp_family":
        from geometry.generators.lamp_generator import generate_lamp_mesh
        return generate_lamp_mesh(genome)
    elif family == "chair_family_lite":
        from geometry.generators.chair_generator import generate_chair_mesh
        return generate_chair_mesh(genome)
    raise ValueError(f"Unknown family: {family}")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_lamp_chair_generators.py -v`
Expected: All 10 tests PASS

- [ ] **Step 7: Commit**

```bash
git add geometry/generators/lamp_generator.py geometry/generators/chair_generator.py geometry/generators/generator_registry.py tests/unit/test_lamp_chair_generators.py
git commit -m "feat: add lamp/chair generators and generator registry"
```

---

## Chunk 4: Validation, Export & CLI Integration

### Task 10: Mesh validator

**Files:**
- Create: `geometry/mesh_validation/validator.py`
- Test: `tests/unit/test_mesh_validator.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_mesh_validator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# geometry/mesh_validation/validator.py
"""Mesh validation and reporting."""

from __future__ import annotations

from dataclasses import dataclass

import trimesh

from config.schemas.config_models import BuildVolume


@dataclass
class MeshReport:
    """Result of mesh validation checks."""

    has_vertices: bool = False
    has_faces: bool = False
    positive_volume: bool = False
    is_watertight: bool = False
    within_build_volume: bool = True
    vertex_count: int = 0
    face_count: int = 0
    volume: float = 0.0

    @property
    def is_acceptable(self) -> bool:
        """Minimum viability: has geometry with positive volume."""
        return self.has_vertices and self.has_faces and self.positive_volume

    def __str__(self) -> str:
        status = "PASS" if self.is_acceptable else "FAIL"
        return (
            f"MeshReport({status}): {self.vertex_count} vertices, "
            f"{self.face_count} faces, volume={self.volume:.1f}, "
            f"watertight={self.is_watertight}, build_vol={self.within_build_volume}"
        )


def validate_mesh(
    mesh: trimesh.Trimesh,
    build_volume: BuildVolume | None = None,
) -> MeshReport:
    """Run validation checks on a mesh and return a report."""
    report = MeshReport()

    report.has_vertices = len(mesh.vertices) > 0
    report.has_faces = len(mesh.faces) > 0
    report.vertex_count = len(mesh.vertices)
    report.face_count = len(mesh.faces)

    if report.has_vertices and report.has_faces:
        try:
            report.volume = float(mesh.volume)
            report.positive_volume = report.volume > 0
        except Exception:
            report.volume = 0.0
            report.positive_volume = False

        report.is_watertight = bool(mesh.is_watertight)

    if build_volume and report.has_vertices:
        extents = mesh.bounding_box.extents
        report.within_build_volume = (
            extents[0] <= build_volume.x
            and extents[1] <= build_volume.y
            and extents[2] <= build_volume.z
        )

    return report
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_mesh_validator.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add geometry/mesh_validation/validator.py tests/unit/test_mesh_validator.py
git commit -m "feat: add mesh validator with MeshReport"
```

---

### Task 11: STL exporter

**Files:**
- Create: `geometry/export/exporter.py`
- Test: `tests/unit/test_exporter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_exporter.py
"""Tests for STL exporter."""

import random

from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from geometry.generators.table_generator import generate_table_mesh
from geometry.export.exporter import export_stl


def test_export_creates_file(tmp_path):
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    out = tmp_path / "test.stl"
    export_stl(mesh, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_export_binary_stl(tmp_path):
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    out = tmp_path / "test.stl"
    export_stl(mesh, out)
    # Binary STL starts with 80-byte header
    data = out.read_bytes()
    assert len(data) > 84


def test_export_with_metadata(tmp_path):
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    out_stl = tmp_path / "test.stl"
    out_json = tmp_path / "test.json"
    export_stl(mesh, out_stl, metadata={"genome_id": genome.genome_id}, metadata_path=out_json)
    assert out_stl.exists()
    assert out_json.exists()

    import json
    meta = json.loads(out_json.read_text())
    assert meta["genome_id"] == genome.genome_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_exporter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# geometry/export/exporter.py
"""Export meshes to STL and metadata to JSON."""

from __future__ import annotations

import json
from pathlib import Path

import trimesh

from core.exceptions import ExportError


def export_stl(
    mesh: trimesh.Trimesh,
    path: Path,
    metadata: dict | None = None,
    metadata_path: Path | None = None,
) -> None:
    """Export mesh as binary STL. Optionally write metadata JSON."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(str(path), file_type="stl")

        if metadata and metadata_path:
            metadata_path = Path(metadata_path)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata, indent=2, default=str))
    except Exception as e:
        raise ExportError(f"STL export failed: {e}", details={"path": str(path)}) from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_exporter.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add geometry/export/exporter.py tests/unit/test_exporter.py
git commit -m "feat: add STL exporter with optional metadata JSON"
```

---

### Task 12: Wire up generate-candidate-once CLI command

**Files:**
- Modify: `dev_cli.py:98-104`
- Test: `tests/unit/test_cli.py` (add new test)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_cli.py`:

```python
def test_generate_candidate_once_produces_output(tmp_path):
    result = runner.invoke(app, [
        "generate-candidate-once",
        "--family", "table_family",
        "--seed", "42",
        "--output-dir", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert "Generated" in result.output
    # Check STL was created
    stl_files = list(tmp_path.glob("*.stl"))
    assert len(stl_files) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_cli.py::test_generate_candidate_once_produces_output -v`
Expected: FAIL — currently stubbed, outputs "Not implemented yet"

- [ ] **Step 3: Update CLI command**

Replace the `generate_candidate_once` function in `dev_cli.py`:

```python
@app.command()
def generate_candidate_once(
    family: str = typer.Option("table_family", "--family", "-f"),
    seed: int = typer.Option(42, "--seed", "-s"),
    output_dir: Path = typer.Option(Path("."), "--output-dir", "-o"),
):
    """Generate a single candidate mesh and export as STL."""
    import random
    from core.genome.catalog_registry import get_catalog
    from core.genome.genome import Genome
    from geometry.generators.generator_registry import generate_mesh
    from geometry.mesh_validation.validator import validate_mesh
    from geometry.export.exporter import export_stl

    try:
        catalog = get_catalog(family)
        rng = random.Random(seed)
        genome = Genome.random_init(catalog, rng)
        mesh = generate_mesh(genome)
        report = validate_mesh(mesh)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        stl_path = output_dir / f"{genome.genome_id}.stl"
        json_path = output_dir / f"{genome.genome_id}.json"
        export_stl(mesh, stl_path, metadata=genome.to_dict(), metadata_path=json_path)

        typer.echo(f"Generated {family} candidate: {genome.genome_id}")
        typer.echo(f"  Mesh: {report}")
        typer.echo(f"  STL:  {stl_path}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_cli.py::test_generate_candidate_once_produces_output -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS (previous 71 + new tests)

- [ ] **Step 6: Commit**

```bash
git add dev_cli.py tests/unit/test_cli.py
git commit -m "feat: wire up generate-candidate-once CLI with full pipeline"
```

---

### Task 13: Batch validation test (exit criteria)

**Files:**
- Create: `tests/integration/test_geometry_batch.py`

- [ ] **Step 1: Write the batch validation test**

```python
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
```

- [ ] **Step 2: Run batch test**

Run: `.venv/bin/python -m pytest tests/integration/test_geometry_batch.py -v`
Expected: All 3 families PASS with >90% valid mesh rate

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_geometry_batch.py
git commit -m "test: add batch validation for >90% mesh success rate across families"
```

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | GeneSpec dataclass | 12 |
| 2 | Genome class | 8 |
| 3 | Table gene catalog | 9 |
| 4 | Lamp + chair catalogs + registry | 10 |
| 5 | Graph builder | 8 |
| 6 | Primitive mesh factories | 10 |
| 7 | Mesh assembler | 4 |
| 8 | Table mesh generator | 6 |
| 9 | Lamp + chair generators + registry | 10 |
| 10 | Mesh validator | 6 |
| 11 | STL exporter | 3 |
| 12 | CLI integration | 1 |
| 13 | Batch exit criteria | 3 |
| **Total** | | **~90 new tests** |

**Exit criteria**: `dev_cli.py generate-candidate-once --family table --seed 42` produces a valid STL. Batch test confirms >90% success across all 3 families.
