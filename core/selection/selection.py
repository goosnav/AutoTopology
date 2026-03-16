"""Selection operators for the evolutionary algorithm.

Implements:
- tournament_select: k-tournament with elitism and invalid exclusion
- select_parents: draw n parents
- get_elites: top-k by combined score (valid only)
"""

from __future__ import annotations

import random
from typing import List

from core.evolution.candidate import Candidate


def tournament_select(
    population: List[Candidate],
    tournament_size: int,
    rng: random.Random,
    physics_weight: float,
    aesthetic_weight: float,
    novelty_weight: float,
) -> Candidate:
    """K-tournament selection, preferring valid candidates.

    Args:
        population: Full population (may include invalid candidates).
        tournament_size: Number of candidates drawn for each tournament.
        rng: Random number generator.
        physics_weight: Weight for physics score.
        aesthetic_weight: Weight for aesthetic score.
        novelty_weight: Weight for novelty score.

    Returns:
        The tournament winner (highest combined score, valid candidates preferred).
    """
    valid = [c for c in population if c.is_valid]
    pool = valid if valid else population  # fallback to all if no valid

    k = min(tournament_size, len(pool))
    contestants = rng.sample(pool, k)
    return max(
        contestants,
        key=lambda c: c.combined_score(physics_weight, aesthetic_weight, novelty_weight),
    )


def select_parents(
    population: List[Candidate],
    n: int,
    tournament_size: int,
    rng: random.Random,
    physics_weight: float,
    aesthetic_weight: float,
    novelty_weight: float,
) -> List[Candidate]:
    """Draw n parents via repeated tournament selection.

    Args:
        population: Full population.
        n: Number of parents to select.
        tournament_size: Tournament size.
        rng: RNG.
        physics_weight: Weight for physics score.
        aesthetic_weight: Weight for aesthetic score.
        novelty_weight: Weight for novelty score.

    Returns:
        List of n selected parents (with replacement).
    """
    return [
        tournament_select(
            population, tournament_size, rng,
            physics_weight, aesthetic_weight, novelty_weight,
        )
        for _ in range(n)
    ]


def get_elites(
    population: List[Candidate],
    k: int,
    physics_weight: float,
    aesthetic_weight: float,
    novelty_weight: float,
) -> List[Candidate]:
    """Return the top-k valid candidates sorted by combined score descending.

    Args:
        population: Full population.
        k: Number of elites to return.
        physics_weight: Weight for physics score.
        aesthetic_weight: Weight for aesthetic score.
        novelty_weight: Weight for novelty score.

    Returns:
        Sorted list of up to k valid candidates.
    """
    valid = [c for c in population if c.is_valid]
    sorted_pop = sorted(
        valid,
        key=lambda c: c.combined_score(physics_weight, aesthetic_weight, novelty_weight),
        reverse=True,
    )
    return sorted_pop[:k]
