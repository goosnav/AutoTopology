"""Genome mutation operators.

Each gene is mutated independently with probability mutation_rate.
Perturbation type depends on GeneType:
- CONTINUOUS: Gaussian perturbation, then clamp to [min, max]
- INTEGER: ±1 random step, clamped
- CATEGORICAL: replace with a random different category (or same if only one)
- BOOLEAN: flip
"""

from __future__ import annotations

import random
import uuid
from typing import List

from core.genome.gene_types import GeneSpec, GeneType
from core.genome.genome import Genome

# Standard deviation as a fraction of the total range for continuous genes
_CONTINUOUS_SIGMA_FRAC = 0.1


def mutate(
    genome: Genome,
    catalog: List[GeneSpec],
    mutation_rate: float,
    rng: random.Random,
) -> Genome:
    """Return a new mutated genome (original is not modified).

    Args:
        genome: Source genome.
        catalog: Gene specifications defining valid ranges.
        mutation_rate: Per-gene mutation probability in [0, 1].
        rng: Random number generator.

    Returns:
        New Genome with mutated genes and a fresh genome_id.
    """
    new_genes = dict(genome.genes)
    catalog_map = {s.name: s for s in catalog}

    for name, value in new_genes.items():
        if rng.random() > mutation_rate:
            continue

        spec = catalog_map.get(name)
        if spec is None:
            continue

        if spec.gene_type == GeneType.CONTINUOUS:
            span = spec.max_val - spec.min_val
            sigma = span * _CONTINUOUS_SIGMA_FRAC
            new_val = value + rng.gauss(0.0, sigma)
            new_val = max(spec.min_val, min(spec.max_val, new_val))
            new_genes[name] = new_val

        elif spec.gene_type == GeneType.INTEGER:
            delta = rng.choice([-1, 1])
            new_val = int(value) + delta
            new_val = max(int(spec.min_val), min(int(spec.max_val), new_val))
            new_genes[name] = new_val

        elif spec.gene_type == GeneType.CATEGORICAL:
            cats = spec.categories
            if len(cats) > 1:
                choices = [c for c in cats if c != value]
                new_genes[name] = rng.choice(choices) if choices else value
            # if only one category, leave as-is

        elif spec.gene_type == GeneType.BOOLEAN:
            new_genes[name] = not value

    return Genome(genes=new_genes, genome_id=uuid.uuid4().hex[:12])
