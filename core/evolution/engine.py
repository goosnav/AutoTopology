"""EvolutionEngine — top-level run-loop orchestrator.

Spec §25: For each generation in each active league/island, step the
evolution, update archives, and invoke optional callbacks.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from core.evolution.candidate import Candidate
from core.leagues.league import League
from core.genome.gene_types import GeneSpec


class EvolutionEngine:
    """Orchestrates multiple leagues across generations.

    Args:
        leagues: List of League objects to evolve.
        catalog: Gene specifications used for novelty etc.
        physics_weight: Fitness weight.
        aesthetic_weight: Fitness weight.
        novelty_weight: Fitness weight.
        n_offspring_per_island: Offspring per island per step.
        on_generation_complete: Optional callback(generation, all_candidates).
    """

    def __init__(
        self,
        leagues: List[League],
        catalog: List[GeneSpec],
        physics_weight: float = 0.4,
        aesthetic_weight: float = 0.4,
        novelty_weight: float = 0.2,
        n_offspring_per_island: int = 10,
        on_generation_complete: Optional[Callable[[int, List[Candidate]], None]] = None,
    ) -> None:
        self.leagues = leagues
        self._catalog = catalog
        self._pw = physics_weight
        self._aw = aesthetic_weight
        self._nw = novelty_weight
        self._n_offspring = n_offspring_per_island
        self.on_generation_complete = on_generation_complete
        self.generation: int = 0

    # ------------------------------------------------------------------ #

    def step(self) -> List[Candidate]:
        """Advance all leagues one generation.

        Returns:
            All current candidates across all leagues.
        """
        for league in self.leagues:
            league.step(
                n_offspring_per_island=self._n_offspring,
                physics_weight=self._pw,
                aesthetic_weight=self._aw,
                novelty_weight=self._nw,
            )

        self.generation += 1
        all_c = self.get_all_candidates()

        if self.on_generation_complete is not None:
            self.on_generation_complete(self.generation, all_c)

        return all_c

    def run(self, n_generations: int) -> None:
        """Run the engine for n_generations steps.

        Args:
            n_generations: Number of generations to evolve.
        """
        for _ in range(n_generations):
            self.step()

    def get_all_candidates(self) -> List[Candidate]:
        """Return all current candidates across all leagues and islands."""
        result: List[Candidate] = []
        for league in self.leagues:
            result.extend(league.all_candidates())
        return result

    def best_candidates(self, k: int) -> List[Candidate]:
        """Return the top-k valid candidates across all leagues, sorted descending.

        Args:
            k: Maximum number to return.

        Returns:
            List of up to k Candidates.
        """
        from core.selection.selection import get_elites
        return get_elites(self.get_all_candidates(), k, self._pw, self._aw, self._nw)
