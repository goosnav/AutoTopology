"""Gallery and candidate detail endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.api import state as app_state

router = APIRouter(prefix="/api", tags=["gallery"])


def _candidate_summary(c) -> dict:
    return {
        "candidate_id": c.candidate_id,
        "family": c.family,
        "physics_score": c.physics_score,
        "aesthetic_score": c.aesthetic_score,
        "novelty_score": c.novelty_score,
        "is_valid": c.is_valid,
        "human_selected": c.human_selected,
        "generation": c.metadata.get("generation"),
        "island_id": c.metadata.get("island_id"),
        "league_id": c.metadata.get("league_id"),
        "subtype": c.genome.genes.get("subtype"),
    }


@router.get("/gallery")
async def gallery(
    sort_by: str = Query("physics", description="Sort key"),
    descending: bool = Query(True),
    valid_only: bool = Query(False),
    family_filter: Optional[str] = Query(None),
    page: int = Query(0, ge=0),
    page_size: Optional[int] = Query(None, gt=0),
):
    """List current gallery candidates with optional sorting / filtering / paging."""
    if app_state.gallery_service is None:
        return {"candidates": [], "total": 0}

    candidates = app_state.gallery_service.list(
        sort_by=sort_by,
        descending=descending,
        valid_only=valid_only,
        family_filter=family_filter,
        page=page,
        page_size=page_size,
    )
    return {
        "candidates": [_candidate_summary(c) for c in candidates],
        "total": app_state.gallery_service.total_count(),
    }


@router.get("/candidate/{candidate_id}")
async def candidate_detail(candidate_id: str):
    """Return full detail for a single candidate."""
    if app_state.gallery_service is None:
        raise HTTPException(status_code=404, detail="No active gallery")

    c = app_state.gallery_service.get_by_id(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")

    return {
        **_candidate_summary(c),
        "genes": c.genome.genes,
        "genome_id": c.genome.genome_id,
        "metadata": c.metadata,
        "taste_bonus": c.taste_bonus,
    }
