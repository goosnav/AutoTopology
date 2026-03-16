"""Island — a semi-independent sub-population that evolves under a fixed EA config.

Each island runs crossover + mutation + selection independently.
Migration happens at the league level via receive_migrants / get_emigrants.
"""

from __future__ import annotations

import random
from typing import Callable, List, Optional

from core.crossover.crossover import uniform_crossover
from core.evolution.candidate import Candidate
from core.genome.gene_types import GeneSpec
from core.genome.genome import Genome
from core.mutation.mutation import mutate
from core.novelty.novelty import compute_novelty_scores
from core.repair.repair import repair_genome
from core.selection.selection import get_elites, select_parents


class Island:
    """A single evolving island.

    Args:
        island_id: Unique string identifier.
        league_id: Owning league's identifier.
        population: Initial list of Candidates.
        catalog: Gene specifications.
        rng: Random number generator.
        mutation_rate: Per-gene mutation probability.
        crossover_rate: Probability of using crossover vs cloning + mutation.
        tournament_size: Tournament size for parent selection.
        elitism_k: Number of elites carried over each generation.
    """

    def __init__(
        self,
        island_id: str,
        league_id: str,
        population: List[Candidate],
        catalog: List[GeneSpec],
        rng: random.Random,
        mutation_rate: float = 0.3,
        crossover_rate: float = 0.7,
        tournament_size: int = 3,
        elitism_k: int = 2,
    ) -> None:
        self.island_id = island_id
        self.league_id = league_id
        self.population: List[Candidate] = list(population)
        self._catalog = catalog
        self._rng = rng
        self._mutation_rate = mutation_rate
        self._crossover_rate = crossover_rate
        self._tournament_size = tournament_size
        self._elitism_k = elitism_k
        self.generation: int = 0

    # ------------------------------------------------------------------ #
    # Core step

    def step(
        self,
        n_offspring: int,
        physics_weight: float,
        aesthetic_weight: float,
        novelty_weight: float,
    ) -> List[Candidate]:
        """Generate one generation of offspring.

        Offspring are produced by:
        1. Elites survive unchanged.
        2. The remainder are produced by crossover+mutation or mutation only.

        Novelty scores are updated for the new combined population.

        Args:
            n_offspring: How many new candidates to produce.
            physics_weight: Fitness weight.
            aesthetic_weight: Fitness weight.
            novelty_weight: Fitness weight.

        Returns:
            The new population (elites + offspring).
        """
        elites = get_elites(
            self.population, self._elitism_k, physics_weight, aesthetic_weight, novelty_weight
        )

        offspring: List[Candidate] = []
        while len(offspring) < n_offspring:
            if self._rng.random() < self._crossover_rate and len(self.population) >= 2:
                parents = select_parents(
                    self.population, n=2,
                    tournament_size=self._tournament_size,
                    rng=self._rng,
                    physics_weight=physics_weight,
                    aesthetic_weight=aesthetic_weight,
                    novelty_weight=novelty_weight,
                )
                try:
                    c1_genome, c2_genome = uniform_crossover(
                        parents[0].genome, parents[1].genome, self._catalog, self._rng
                    )
                except Exception:
                    # Incompatible parents — fall back to mutation
                    c1_genome = mutate(parents[0].genome, self._catalog, self._mutation_rate, self._rng)
                    c2_genome = mutate(parents[1].genome, self._catalog, self._mutation_rate, self._rng)

                c1_genome = mutate(c1_genome, self._catalog, self._mutation_rate, self._rng)
                c2_genome = mutate(c2_genome, self._catalog, self._mutation_rate, self._rng)
                c1_genome = repair_genome(c1_genome, self._catalog)
                c2_genome = repair_genome(c2_genome, self._catalog)

                offspring.append(self._wrap(c1_genome, parents[0]))
                if len(offspring) < n_offspring:
                    offspring.append(self._wrap(c2_genome, parents[1]))
            else:
                parent = select_parents(
                    self.population, n=1,
                    tournament_size=self._tournament_size,
                    rng=self._rng,
                    physics_weight=physics_weight,
                    aesthetic_weight=aesthetic_weight,
                    novelty_weight=novelty_weight,
                )[0]
                new_genome = mutate(parent.genome, self._catalog, self._mutation_rate, self._rng)
                new_genome = repair_genome(new_genome, self._catalog)
                offspring.append(self._wrap(new_genome, parent))

        new_population = elites + offspring

        # Update novelty scores
        self._update_novelty(new_population)

        self.population = new_population
        self.generation += 1
        return new_population

    def _wrap(self, genome: Genome, parent: Candidate) -> Candidate:
        """Wrap a new genome into a Candidate inheriting parent's family."""
        return Candidate(
            genome=genome,
            family=parent.family,
            # Physics / aesthetic scores are 0.0 until evaluated
            physics_score=0.0,
            aesthetic_score=0.0,
            novelty_score=0.0,
            is_valid=True,  # Assumed valid until evaluated
        )

    def _update_novelty(self, population: List[Candidate]) -> None:
        """Re-score novelty across the full population in-place."""
        genomes = [c.genome for c in population]
        scores = compute_novelty_scores(genomes, self._catalog, k=min(5, len(genomes) - 1))
        for c, s in zip(population, scores):
            c.novelty_score = s

    # ------------------------------------------------------------------ #
    # Migration API

    def receive_migrants(self, migrants: List[Candidate]) -> None:
        """Add migrants to this island's population."""
        self.population.extend(migrants)

    def get_emigrants(
        self,
        n: int,
        physics_weight: float,
        aesthetic_weight: float,
        novelty_weight: float,
    ) -> List[Candidate]:
        """Return the top-n candidates as emigrants (does not remove them)."""
        return get_elites(self.population, n, physics_weight, aesthetic_weight, novelty_weight)
