"""Candidate — a fully-evaluated genome with scores and metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from core.genome.genome import Genome

# Boost factor applied to combined score when a human has selected this candidate
_HUMAN_BOOST = 0.15


@dataclass
class Candidate:
    """A genome paired with its evaluation scores.

    Scores are normalised floats in [0, 1].
    Invalid candidates (failed hard gates) report combined_score == 0.
    """

    genome: Genome
    family: str

    # Scores — set after evaluation; None means not yet evaluated
    physics_score: float = 0.0
    aesthetic_score: float = 0.0
    novelty_score: float = 0.0
    taste_bonus: float = 0.0

    # Hard gates
    is_valid: bool = True

    # Human preference
    human_selected: bool = False

    # Unique ID distinct from genome_id (a candidate wraps one genome instance)
    candidate_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    # Optional metadata blob
    metadata: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #

    def combined_score(
        self,
        physics_weight: float,
        aesthetic_weight: float,
        novelty_weight: float,
    ) -> float:
        """Weighted combined fitness.

        Returns 0.0 for invalid candidates (they must not compete as elites).
        Applies a human-selection boost when human_selected is True.
        """
        if not self.is_valid:
            return 0.0

        raw = (
            self.physics_score * physics_weight
            + self.aesthetic_score * aesthetic_weight
            + self.novelty_score * novelty_weight
            + self.taste_bonus
        )

        if self.human_selected:
            raw = min(1.0, raw + _HUMAN_BOOST)

        return raw

    # ------------------------------------------------------------------ #
    # Serialisation

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "family": self.family,
            "genome": self.genome.to_dict(),
            "physics_score": self.physics_score,
            "aesthetic_score": self.aesthetic_score,
            "novelty_score": self.novelty_score,
            "taste_bonus": self.taste_bonus,
            "is_valid": self.is_valid,
            "human_selected": self.human_selected,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Candidate:
        return cls(
            genome=Genome.from_dict(data["genome"]),
            family=data["family"],
            physics_score=data["physics_score"],
            aesthetic_score=data["aesthetic_score"],
            novelty_score=data["novelty_score"],
            taste_bonus=data.get("taste_bonus", 0.0),
            is_valid=data["is_valid"],
            human_selected=data.get("human_selected", False),
            candidate_id=data["candidate_id"],
            metadata=data.get("metadata", {}),
        )
