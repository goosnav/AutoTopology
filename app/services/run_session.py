"""RunSession — manages a single evolution run's lifecycle.

States:
  IDLE → RUNNING → PAUSED → RUNNING ...
                 ↘ STOPPED

Spec §25: The run loop must pause at safe review boundaries after all
evaluations for the current generation are complete.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from core.evolution.engine import EvolutionEngine


class RunState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class RunSessionError(Exception):
    """Raised on illegal state transitions."""


class RunSession:
    """Wraps an EvolutionEngine with start/pause/resume/stop lifecycle.

    Args:
        engine: Pre-configured EvolutionEngine.
        review_every_n_generations: How many generations between review boundaries.
    """

    def __init__(self, engine: EvolutionEngine, review_every_n_generations: int = 5) -> None:
        self.engine = engine
        self.review_every_n_generations = review_every_n_generations
        self.state: RunState = RunState.IDLE

    # ------------------------------------------------------------------ #
    # State transitions

    def start(self) -> None:
        """Transition from IDLE to RUNNING."""
        if self.state != RunState.IDLE:
            raise RunSessionError(
                f"Cannot start: session is already in state '{self.state}'"
            )
        self.state = RunState.RUNNING

    def pause(self) -> None:
        """Transition from RUNNING to PAUSED (e.g. at a review boundary)."""
        if self.state != RunState.RUNNING:
            raise RunSessionError(f"Cannot pause: current state is '{self.state}'")
        self.state = RunState.PAUSED

    def resume(self) -> None:
        """Transition from PAUSED back to RUNNING."""
        if self.state != RunState.PAUSED:
            raise RunSessionError(f"Cannot resume: current state is '{self.state}'")
        self.state = RunState.RUNNING

    def stop(self) -> None:
        """Terminate the session from any active state."""
        if self.state == RunState.STOPPED:
            return
        if self.state == RunState.IDLE:
            raise RunSessionError("Cannot stop a session that was never started")
        self.state = RunState.STOPPED

    # ------------------------------------------------------------------ #
    # Execution

    def step(self) -> None:
        """Advance the engine by one generation.

        Raises:
            RunSessionError: If the session is not in RUNNING state.
        """
        if self.state not in (RunState.RUNNING,):
            raise RunSessionError(
                f"Cannot step: session state is '{self.state}'"
            )
        self.engine.step()

    # ------------------------------------------------------------------ #
    # Introspection

    def at_review_boundary(self) -> bool:
        """True if the current generation is a review boundary."""
        gen = self.engine.generation
        return gen > 0 and (gen % self.review_every_n_generations == 0)

    def status(self) -> dict[str, Any]:
        """Return a plain-dict summary of the session."""
        all_candidates = self.engine.get_all_candidates()
        return {
            "state": self.state.value,
            "generation": self.engine.generation,
            "candidate_count": len(all_candidates),
            "at_review_boundary": self.at_review_boundary(),
        }
