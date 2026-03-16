"""Crossover operators for the evolutionary algorithm.

Spec §24.3: crossover must be compatibility-aware (same family only).

Operators:
- uniform_crossover: each gene independently inherited from either parent
- single_point_crossover: genes before/after a random cut come from different parents
"""

from __future__ import annotations

import random
import uuid
from typing import List, Tuple

from core.genome.gene_types import GeneSpec
from core.genome.genome import Genome


class CrossoverError(Exception):
    """Raised when parents are incompatible for crossover."""


def _check_compatibility(p1: Genome, p2: Genome) -> None:
    """Raise CrossoverError if genomes are from different families."""
    f1 = p1.genes.get("family_name")
    f2 = p2.genes.get("family_name")
    if f1 is not None and f2 is not None and f1 != f2:
        raise CrossoverError(
            f"Cannot cross genomes from different families: '{f1}' vs '{f2}'"
        )


def uniform_crossover(
    parent1: Genome,
    parent2: Genome,
    catalog: List[GeneSpec],
    rng: random.Random,
    swap_prob: float = 0.5,
) -> Tuple[Genome, Genome]:
    """Uniform crossover: each gene independently inherited from either parent.

    Args:
        parent1: First parent genome.
        parent2: Second parent genome.
        catalog: Gene specifications (unused here but kept for API consistency).
        rng: Random number generator.
        swap_prob: Probability that child1 takes a gene from parent2 (and vice versa).

    Returns:
        Two new child genomes.

    Raises:
        CrossoverError: If parents have different family_name genes.
    """
    _check_compatibility(parent1, parent2)

    all_keys = list(dict.fromkeys(list(parent1.genes.keys()) + list(parent2.genes.keys())))

    child1_genes: dict = {}
    child2_genes: dict = {}

    for key in all_keys:
        v1 = parent1.genes.get(key)
        v2 = parent2.genes.get(key)

        if rng.random() < swap_prob:
            child1_genes[key] = v2 if v2 is not None else v1
            child2_genes[key] = v1 if v1 is not None else v2
        else:
            child1_genes[key] = v1 if v1 is not None else v2
            child2_genes[key] = v2 if v2 is not None else v1

    return (
        Genome(genes=child1_genes, genome_id=uuid.uuid4().hex[:12]),
        Genome(genes=child2_genes, genome_id=uuid.uuid4().hex[:12]),
    )


def single_point_crossover(
    parent1: Genome,
    parent2: Genome,
    catalog: List[GeneSpec],
    rng: random.Random,
) -> Tuple[Genome, Genome]:
    """Single-point crossover: genes before cut come from p1, after from p2 (and vice versa).

    Args:
        parent1: First parent genome.
        parent2: Second parent genome.
        catalog: Gene specifications (used for stable gene ordering).
        rng: Random number generator.

    Returns:
        Two new child genomes.

    Raises:
        CrossoverError: If parents have different family_name genes.
    """
    _check_compatibility(parent1, parent2)

    # Use catalog order for a stable cut point
    keys = [s.name for s in catalog]
    if not keys:
        keys = list(parent1.genes.keys())

    cut = rng.randint(1, max(1, len(keys) - 1))

    child1_genes: dict = {}
    child2_genes: dict = {}

    for i, key in enumerate(keys):
        v1 = parent1.genes.get(key)
        v2 = parent2.genes.get(key)
        if i < cut:
            child1_genes[key] = v1 if v1 is not None else v2
            child2_genes[key] = v2 if v2 is not None else v1
        else:
            child1_genes[key] = v2 if v2 is not None else v1
            child2_genes[key] = v1 if v1 is not None else v2

    return (
        Genome(genes=child1_genes, genome_id=uuid.uuid4().hex[:12]),
        Genome(genes=child2_genes, genome_id=uuid.uuid4().hex[:12]),
    )
