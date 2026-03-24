"""ReviewService — human top-K selection and pairwise tie-breaks.

Spec §17: Human selections strongly boost survival but must not override hard invalidity.
"""

from __future__ import annotations

import time
from typing import List, Optional

from core.evolution.candidate import Candidate


class ReviewError(Exception):
    """Raised when a review operation references an unknown candidate."""


class ReviewService:
    """Manages the human review state for one review boundary.

    Args:
        candidates: The pool of candidates presented to the user.
    """

    def __init__(self, candidates: List[Candidate]) -> None:
        self.candidates = list(candidates)
        self._id_map: dict[str, Candidate] = {c.candidate_id: c for c in self.candidates}
        self._pairwise_history: list[dict] = []

    # ------------------------------------------------------------------ #

    def _resolve(self, candidate_id: str) -> Candidate:
        c = self._id_map.get(candidate_id)
        if c is None:
            raise ReviewError(f"Unknown candidate ID: '{candidate_id}'")
        return c

    # ------------------------------------------------------------------ #

    def submit_top_k(self, candidate_ids: List[str]) -> None:
        """Mark candidates as human-selected, boosting their combined score.

        Args:
            candidate_ids: IDs of the chosen candidates.

        Raises:
            ReviewError: If any ID is not in the current candidate pool.
        """
        for cid in candidate_ids:
            c = self._resolve(cid)
            c.human_selected = True

    def submit_pairwise(self, winner_id: str, loser_id: str) -> None:
        """Record a pairwise preference: winner > loser.

        Appends to pairwise history (used for taste-model training).

        Args:
            winner_id: The preferred candidate.
            loser_id: The non-preferred candidate.

        Raises:
            ReviewError: If either ID is unknown.
        """
        winner = self._resolve(winner_id)
        loser = self._resolve(loser_id)
        self._pairwise_history.append({
            "winner": winner.candidate_id,
            "loser": loser.candidate_id,
            "ts": time.time(),
        })

    def get_shortlist(self) -> List[Candidate]:
        """Return all candidates that have been human-selected."""
        return [c for c in self.candidates if c.human_selected]

    def get_pairwise_history(self) -> list[dict]:
        """Return the pairwise preference history for this review."""
        return list(self._pairwise_history)

    def clear(self) -> None:
        """Reset all human selections and pairwise history."""
        for c in self.candidates:
            c.human_selected = False
        self._pairwise_history.clear()
