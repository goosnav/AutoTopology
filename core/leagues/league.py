"""League — a group of islands that evolve together with periodic migration.

Spec §20: Each league has distinct mutation/crossover biases, a leaderboard,
and triggers migration at configured intervals.
"""

from __future__ import annotations

import random
from typing import List, Optional

from core.evolution.candidate import Candidate
from core.leagues.island import Island
from core.selection.selection import get_elites


class League:
    """A collection of islands that share a leaderboard and periodic migration.

    Args:
        league_id: Unique identifier.
        islands: List of Island objects belonging to this league.
        migration_rate: Fraction of each island's population to migrate.
        migration_interval: How many generations between migrations.
    """

    def __init__(
        self,
        league_id: str,
        islands: List[Island],
        migration_rate: float = 0.1,
        migration_interval: int = 3,
    ) -> None:
        self.league_id = league_id
        self.islands = islands
        self.migration_rate = migration_rate
        self.migration_interval = migration_interval
        self.generation: int = 0

    # ------------------------------------------------------------------ #

    def step(
        self,
        n_offspring_per_island: int,
        physics_weight: float,
        aesthetic_weight: float,
        novelty_weight: float,
    ) -> None:
        """Advance all islands one generation and apply migration if scheduled.

        Args:
            n_offspring_per_island: Offspring count passed to each island.
            physics_weight: Fitness weight.
            aesthetic_weight: Fitness weight.
            novelty_weight: Fitness weight.
        """
        for island in self.islands:
            island.step(
                n_offspring=n_offspring_per_island,
                physics_weight=physics_weight,
                aesthetic_weight=aesthetic_weight,
                novelty_weight=novelty_weight,
            )

        self.generation += 1

        if self.generation % self.migration_interval == 0:
            self._migrate(physics_weight, aesthetic_weight, novelty_weight)

    def _migrate(
        self,
        physics_weight: float,
        aesthetic_weight: float,
        novelty_weight: float,
    ) -> None:
        """Ring migration: each island sends emigrants to the next island."""
        if len(self.islands) < 2:
            return

        n_migrants = max(1, int(
            len(self.islands[0].population) * self.migration_rate
        ))

        # Gather emigrants first, then distribute (ring topology)
        all_emigrants: List[List[Candidate]] = []
        for island in self.islands:
            emigrants = island.get_emigrants(
                n=n_migrants,
                physics_weight=physics_weight,
                aesthetic_weight=aesthetic_weight,
                novelty_weight=novelty_weight,
            )
            all_emigrants.append(emigrants)

        for i, island in enumerate(self.islands):
            source = all_emigrants[(i - 1) % len(self.islands)]
            island.receive_migrants(source)

    # ------------------------------------------------------------------ #

    def leaderboard(
        self,
        k: int,
        physics_weight: float,
        aesthetic_weight: float,
        novelty_weight: float,
    ) -> List[Candidate]:
        """Return top-k valid candidates across all islands, sorted by score.

        Args:
            k: Maximum number of candidates to return.
            physics_weight: Fitness weight.
            aesthetic_weight: Fitness weight.
            novelty_weight: Fitness weight.

        Returns:
            Sorted list of up to k Candidates.
        """
        all_candidates: List[Candidate] = []
        for island in self.islands:
            all_candidates.extend(island.population)

        return get_elites(all_candidates, k, physics_weight, aesthetic_weight, novelty_weight)

    def all_candidates(self) -> List[Candidate]:
        """Return all candidates across all islands."""
        result: List[Candidate] = []
        for island in self.islands:
            result.extend(island.population)
        return result
