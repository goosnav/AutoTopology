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
