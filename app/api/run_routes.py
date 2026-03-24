"""Run control endpoints: start, pause, resume, stop, step, status."""

from __future__ import annotations

import random
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api import state as app_state

router = APIRouter(prefix="/api/run", tags=["run"])


# ------------------------------------------------------------------ #
# Request schemas

class StartRunRequest(BaseModel):
    family: str = "table_family"
    population_count: int = Field(default=20, gt=0)
    islands_per_league: int = Field(default=2, gt=0)
    league_count: int = Field(default=1, gt=0)
    review_every_n_generations: int = Field(default=5, gt=0)
    mutation_rate: float = Field(default=0.3, gt=0, le=1)
    crossover_rate: float = Field(default=0.7, gt=0, le=1)
    n_offspring_per_island: int = Field(default=10, gt=0)
    seed: Optional[int] = None


# ------------------------------------------------------------------ #
# Helpers

def _build_session(req: StartRunRequest):
    from core.evolution.engine import EvolutionEngine
    from core.genome.catalog_registry import get_catalog
    from core.genome.genome import Genome
    from core.leagues.island import Island
    from core.leagues.league import League
    from core.evolution.candidate import Candidate
    from app.services.run_session import RunSession

    seed = req.seed if req.seed is not None else random.randint(0, 2**31)
    rng_root = random.Random(seed)
    catalog = get_catalog(req.family)

    pop_per_island = max(2, req.population_count // max(1, req.islands_per_league * req.league_count))

    leagues = []
    for li in range(req.league_count):
        islands = []
        for ii in range(req.islands_per_league):
            island_rng = random.Random(rng_root.randint(0, 2**31))
            pop = [
                Candidate(
                    genome=Genome.random_init(catalog, random.Random(rng_root.randint(0, 2**31))),
                    family=req.family,
                )
                for _ in range(pop_per_island)
            ]
            islands.append(Island(
                island_id=f"i{li}_{ii}",
                league_id=f"l{li}",
                population=pop,
                catalog=catalog,
                rng=island_rng,
                mutation_rate=req.mutation_rate,
                crossover_rate=req.crossover_rate,
            ))
        leagues.append(League(
            league_id=f"l{li}",
            islands=islands,
            migration_rate=0.1,
            migration_interval=3,
        ))

    engine = EvolutionEngine(
        leagues=leagues,
        catalog=catalog,
        n_offspring_per_island=req.n_offspring_per_island,
    )
    return RunSession(engine=engine, review_every_n_generations=req.review_every_n_generations)


def _init_services(session) -> None:
    """Initialise gallery, review, and export services after session creation."""
    from app.services.gallery_service import GalleryService
    from app.services.review_service import ReviewService
    from app.services.export_service import ExportService

    all_candidates = session.engine.get_all_candidates()
    app_state.gallery_service = GalleryService(candidates=all_candidates)
    app_state.review_service = ReviewService(candidates=all_candidates)
    app_state.export_service = ExportService(
        export_dir=Path(tempfile.gettempdir()) / "autotopology_exports"
    )


def _refresh_gallery() -> None:
    """Sync gallery with latest engine candidates."""
    if app_state.run_session and app_state.gallery_service:
        app_state.gallery_service.update(
            app_state.run_session.engine.get_all_candidates()
        )


# ------------------------------------------------------------------ #
# Endpoints

@router.get("/status")
async def run_status():
    """Return current run state and generation info."""
    if app_state.run_session is None:
        return {"state": "idle", "generation": 0, "candidate_count": 0, "at_review_boundary": False}
    return app_state.run_session.status()


@router.post("/start")
async def run_start(req: StartRunRequest):
    """Create and start a new evolution run."""
    from app.services.run_session import RunSessionError

    # Stop existing session if any
    if app_state.run_session is not None:
        try:
            app_state.run_session.stop()
        except RunSessionError:
            pass

    session = _build_session(req)
    app_state.run_session = session
    _init_services(session)
    session.start()
    return session.status()


@router.post("/pause")
async def run_pause():
    """Pause the current run."""
    from app.services.run_session import RunSessionError
    if app_state.run_session is None:
        raise HTTPException(status_code=400, detail="No active run session")
    try:
        app_state.run_session.pause()
    except RunSessionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return app_state.run_session.status()


@router.post("/resume")
async def run_resume():
    """Resume a paused run."""
    from app.services.run_session import RunSessionError
    if app_state.run_session is None:
        raise HTTPException(status_code=400, detail="No active run session")
    try:
        app_state.run_session.resume()
    except RunSessionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return app_state.run_session.status()


@router.post("/stop")
async def run_stop():
    """Stop the current run."""
    from app.services.run_session import RunSessionError
    if app_state.run_session is None:
        raise HTTPException(status_code=400, detail="No active run session")
    try:
        app_state.run_session.stop()
    except RunSessionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return app_state.run_session.status()


@router.post("/step")
async def run_step():
    """Advance one generation (primarily for testing / manual stepping)."""
    from app.services.run_session import RunSessionError
    if app_state.run_session is None:
        raise HTTPException(status_code=400, detail="No active run session")
    try:
        app_state.run_session.step()
    except RunSessionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _refresh_gallery()
    return app_state.run_session.status()
