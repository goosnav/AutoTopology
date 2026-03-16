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
