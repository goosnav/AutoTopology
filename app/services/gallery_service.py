"""GalleryService — filtering, sorting, and paging of candidate collections.

Spec §17.2: The user must be able to sort by fitness, novelty, family subtype,
island, league, or generation.
"""

from __future__ import annotations

from typing import List, Optional

from core.evolution.candidate import Candidate

_SORT_KEYS = {
    "physics": lambda c: c.physics_score,
    "aesthetic": lambda c: c.aesthetic_score,
    "novelty": lambda c: c.novelty_score,
    "family": lambda c: c.family,
    "subtype": lambda c: c.genome.genes.get("subtype", ""),
    "island": lambda c: c.metadata.get("island_id", ""),
    "league": lambda c: c.metadata.get("league_id", ""),
    "generation": lambda c: c.metadata.get("generation", 0),
}


class GalleryService:
    """Provides filtered / sorted / paged views over a candidate list.

    Args:
        candidates: The full list of candidates to serve.
    """

    def __init__(self, candidates: List[Candidate]) -> None:
        self._candidates = list(candidates)

    # ------------------------------------------------------------------ #

    def list(
        self,
        sort_by: str = "physics",
        descending: bool = True,
        valid_only: bool = False,
        family_filter: Optional[str] = None,
        page: int = 0,
        page_size: Optional[int] = None,
    ) -> List[Candidate]:
        """Return a filtered, sorted, paged view of candidates.

        Args:
            sort_by: Sort key — one of physics, aesthetic, novelty, family,
                     subtype, island, league, generation.
            descending: Sort direction.
            valid_only: If True, exclude invalid candidates.
            family_filter: If set, include only candidates from this family.
            page: Zero-based page number (used only if page_size is set).
            page_size: Number of items per page. None = return all.

        Returns:
            Filtered, sorted, and paged candidate list.
        """
        result = self._candidates

        if valid_only:
            result = [c for c in result if c.is_valid]

        if family_filter is not None:
            result = [c for c in result if c.family == family_filter]

        key_fn = _SORT_KEYS.get(sort_by, _SORT_KEYS["physics"])
        result = sorted(result, key=key_fn, reverse=descending)

        if page_size is not None:
            start = page * page_size
            result = result[start: start + page_size]

        return result

    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Return the candidate with the given ID, or None."""
        for c in self._candidates:
            if c.candidate_id == candidate_id:
                return c
        return None

    def total_count(self) -> int:
        """Total number of candidates in the gallery."""
        return len(self._candidates)

    def update(self, candidates: List[Candidate]) -> None:
        """Replace the entire candidate list (e.g. after a new generation)."""
        self._candidates = list(candidates)
