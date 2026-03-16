"""Novelty scoring via k-nearest-neighbour genome distance.

Spec §23: minimal V1 novelty from genome descriptor distance.
"""

from __future__ import annotations

import math
from typing import List

from core.genome.gene_types import GeneSpec, GeneType
from core.genome.genome import Genome


def genome_distance(
    g1: Genome,
    g2: Genome,
    catalog: List[GeneSpec],
) -> float:
    """Normalised Euclidean distance between two genomes over all genes.

    Each dimension is normalised to [0, 1] before combining:
    - CONTINUOUS / INTEGER: (v - min) / (max - min)
    - CATEGORICAL: 0 if same, 1 if different
    - BOOLEAN: 0 if same, 1 if different

    Returns a float in [0, 1].
    """
    dims: list[float] = []
    for spec in catalog:
        v1 = g1.genes.get(spec.name)
        v2 = g2.genes.get(spec.name)
        if v1 is None or v2 is None:
            dims.append(0.0)
            continue

        if spec.gene_type in (GeneType.CONTINUOUS, GeneType.INTEGER):
            span = spec.max_val - spec.min_val
            if span == 0:
                dims.append(0.0)
            else:
                n1 = (v1 - spec.min_val) / span
                n2 = (v2 - spec.min_val) / span
                dims.append(abs(n1 - n2))
        elif spec.gene_type == GeneType.CATEGORICAL:
            dims.append(0.0 if v1 == v2 else 1.0)
        elif spec.gene_type == GeneType.BOOLEAN:
            dims.append(0.0 if v1 == v2 else 1.0)

    if not dims:
        return 0.0

    # Normalised Euclidean: divide by sqrt(n) so range stays [0,1]
    sq_sum = sum(d * d for d in dims)
    return math.sqrt(sq_sum / len(dims))


def compute_novelty_scores(
    population: List[Genome],
    catalog: List[GeneSpec],
    k: int = 5,
) -> List[float]:
    """Compute novelty for each genome as average distance to its k nearest neighbours.

    Args:
        population: List of genomes.
        catalog: Gene specifications.
        k: Number of nearest neighbours.

    Returns:
        List of novelty floats in [0, 1], one per genome, in the same order.
    """
    n = len(population)
    if n <= 1:
        return [0.0] * n

    k_actual = min(k, n - 1)
    scores: list[float] = []

    for i, g in enumerate(population):
        dists = sorted(
            genome_distance(g, population[j], catalog)
            for j in range(n)
            if j != i
        )
        avg_dist = sum(dists[:k_actual]) / k_actual
        scores.append(avg_dist)

    # Normalise to [0, 1] by the max observed distance
    max_s = max(scores) if scores else 1.0
    if max_s == 0.0:
        return [0.0] * n
    return [s / max_s for s in scores]
