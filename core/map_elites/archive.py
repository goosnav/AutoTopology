"""MAP-Elites archive — quality-diversity layer preserving diverse design types.

Spec §21: For each descriptor cell, keep the best valid candidate by combined
ranking score.  Descriptor axes are specified by gene name; values are
discretised into bins.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from core.evolution.candidate import Candidate


class MAPElitesArchive:
    """Discrete MAP-Elites archive using gene values as descriptor axes.

    Args:
        descriptor_keys: Gene names to use as descriptor axes.
        bins_per_axis: Number of discrete bins per axis.
        physics_weight: Weight used when comparing candidates in the same cell.
        aesthetic_weight: Weight used when comparing candidates in the same cell.
        novelty_weight: Weight used when comparing candidates in the same cell.
    """

    def __init__(
        self,
        descriptor_keys: List[str],
        bins_per_axis: int = 5,
        physics_weight: float = 0.4,
        aesthetic_weight: float = 0.4,
        novelty_weight: float = 0.2,
    ) -> None:
        self._keys = descriptor_keys
        self._bins = bins_per_axis
        self._pw = physics_weight
        self._aw = aesthetic_weight
        self._nw = novelty_weight

        # cell_key → Candidate
        self._cells: dict[tuple, Candidate] = {}

        # Observed value ranges per descriptor key for float normalisation
        self._ranges: dict[str, tuple[float, float]] = {}

    # ------------------------------------------------------------------ #

    def _update_range(self, key: str, value: float) -> None:
        """Track observed min/max per descriptor key for normalisation."""
        lo, hi = self._ranges.get(key, (value, value))
        self._ranges[key] = (min(lo, value), max(hi, value))

    def _cell_key(self, candidate: Candidate) -> tuple:
        """Map a candidate to a discrete cell tuple.

        Floats are range-normalised using observed min/max (updated on insert).
        This avoids all values falling into the same bin when they share a common factor.
        """
        # First pass: update ranges for float/int keys
        for key in self._keys:
            value = candidate.genome.genes.get(key)
            if value is None:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self._update_range(key, float(value))

        parts: List[int] = []
        for key in self._keys:
            value = candidate.genome.genes.get(key)
            if value is None:
                parts.append(0)
                continue

            if isinstance(value, bool):
                parts.append(int(value))
            elif isinstance(value, (int, float)):
                lo, hi = self._ranges.get(key, (float(value), float(value)))
                span = hi - lo
                if span == 0:
                    parts.append(0)
                else:
                    normalised = (float(value) - lo) / span  # [0, 1]
                    bin_idx = min(int(normalised * self._bins), self._bins - 1)
                    parts.append(bin_idx)
            elif isinstance(value, str):
                parts.append(abs(hash(value)) % self._bins)
            else:
                parts.append(0)
        return tuple(parts)

    def try_insert(self, candidate: Candidate) -> bool:
        """Attempt to insert a candidate into its cell.

        Only valid candidates are accepted.  Replaces the current occupant only
        if the new candidate has a higher combined score.

        Returns:
            True if the candidate was inserted (new or replacement), else False.
        """
        if not candidate.is_valid:
            return False

        key = self._cell_key(candidate)
        existing = self._cells.get(key)

        if existing is None:
            self._cells[key] = candidate
            return True

        new_score = candidate.combined_score(self._pw, self._aw, self._nw)
        old_score = existing.combined_score(self._pw, self._aw, self._nw)

        if new_score > old_score:
            self._cells[key] = candidate
            return True

        return False

    def size(self) -> int:
        """Number of occupied cells."""
        return len(self._cells)

    def get_best(self) -> List[Candidate]:
        """Return all archive occupants sorted by combined score descending."""
        return sorted(
            self._cells.values(),
            key=lambda c: c.combined_score(self._pw, self._aw, self._nw),
            reverse=True,
        )

    def random_sample(self, n: int, rng: random.Random) -> List[Candidate]:
        """Return up to n randomly sampled archive occupants."""
        occupants = list(self._cells.values())
        if not occupants:
            return []
        k = min(n, len(occupants))
        return rng.sample(occupants, k)

    def all_candidates(self) -> List[Candidate]:
        return list(self._cells.values())
