"""Score orchestrator — manages VLM scoring with caching, retry, and fallback.

Spec (§15.7 / §15.8):
- Cache scored results by candidate hash (avoids re-scoring)
- Track global failure rate; halt run when threshold exceeded
- Fallback modes: "fail" | "physics_only" | "cached"
- Reset stats between runs if needed
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PIL import Image

from vision.adapters.vlm_loader import VLMAdapter


class VLMScoringError(Exception):
    """Raised when VLM scoring fails and the configured mode requires a halt."""


class ScoreOrchestrator:
    """Orchestrates VLM scoring with in-memory + disk cache and failure tracking.

    Args:
        adapter: VLMAdapter instance (or mock).
        cache_dir: Optional directory for persisting score cache as JSON files.
        failure_rate_threshold: Fraction [0,1] of failures that triggers a halt.
        fallback_mode: "fail" | "physics_only" | "cached".
    """

    def __init__(
        self,
        adapter: VLMAdapter,
        cache_dir: Optional[Path],
        failure_rate_threshold: float = 0.5,
        fallback_mode: str = "physics_only",
    ) -> None:
        self._adapter = adapter
        self._cache_dir = cache_dir
        self._failure_rate_threshold = failure_rate_threshold
        self._fallback_mode = fallback_mode

        # In-memory cache: hash → score dict
        self._cache: dict[str, dict[str, float]] = {}

        # Stats
        self._total = 0
        self._failures = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def failure_count(self) -> int:
        return self._failures

    @property
    def total_count(self) -> int:
        return self._total

    def score(
        self,
        image: Image.Image,
        candidate_hash: str,
    ) -> Optional[dict[str, float]]:
        """Score an image, using cache if available.

        Args:
            image: PIL Image of the 4-view collage.
            candidate_hash: Unique hash identifying this candidate.

        Returns:
            Score dict, or None if failure and fallback_mode is "physics_only".

        Raises:
            VLMScoringError: If failure_mode is "fail" and scoring fails, or
                             if the global failure rate exceeds the threshold.
        """
        # Check cache first
        cached = self._load_cache(candidate_hash)
        if cached is not None:
            return cached

        # Check failure rate before attempting
        self._check_failure_rate()

        # Attempt scoring
        result = self._adapter.score_image(image)
        self._total += 1

        if result.success:
            self._store_cache(candidate_hash, result.scores)
            return result.scores

        # Handle failure
        self._failures += 1
        return self._handle_failure(candidate_hash, result.error or "unknown error")

    def reset_stats(self) -> None:
        """Reset failure/total counters (call between independent runs)."""
        self._total = 0
        self._failures = 0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    # Minimum scored candidates before rate enforcement kicks in
    _MIN_SAMPLES_FOR_RATE_CHECK = 3

    def _check_failure_rate(self) -> None:
        """Raise VLMScoringError if current failure rate exceeds threshold."""
        if self._total < self._MIN_SAMPLES_FOR_RATE_CHECK:
            return
        rate = self._failures / self._total
        if rate > self._failure_rate_threshold:
            raise VLMScoringError(
                f"VLM failure rate {rate:.1%} exceeds threshold "
                f"{self._failure_rate_threshold:.1%} "
                f"({self._failures}/{self._total} failures)"
            )

    def _handle_failure(
        self,
        candidate_hash: str,
        error: str,
    ) -> Optional[dict[str, float]]:
        if self._fallback_mode == "fail":
            raise VLMScoringError(f"VLM scoring failed for {candidate_hash}: {error}")

        if self._fallback_mode == "cached":
            cached = self._load_cache(candidate_hash)
            if cached is not None:
                return cached
            # No cache available — degrade to None (same as physics_only)

        # physics_only or cached-with-no-cache: return None
        return None

    def _cache_path(self, candidate_hash: str) -> Optional[Path]:
        if self._cache_dir is None:
            return None
        return self._cache_dir / f"{candidate_hash}.scores.json"

    def _load_cache(self, candidate_hash: str) -> Optional[dict[str, float]]:
        # In-memory first
        if candidate_hash in self._cache:
            return self._cache[candidate_hash]
        # Disk cache
        path = self._cache_path(candidate_hash)
        if path is not None and path.exists():
            try:
                data = json.loads(path.read_text())
                self._cache[candidate_hash] = data
                return data
            except Exception:
                pass
        return None

    def _store_cache(
        self,
        candidate_hash: str,
        scores: dict[str, float],
    ) -> None:
        self._cache[candidate_hash] = scores
        path = self._cache_path(candidate_hash)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(scores))
