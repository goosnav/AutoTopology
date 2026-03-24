"""Review endpoints: top-K selection and pairwise tie-breaks."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api import state as app_state

router = APIRouter(prefix="/api/review", tags=["review"])


class TopKRequest(BaseModel):
    candidate_ids: List[str]


class PairwiseRequest(BaseModel):
    winner_id: str
    loser_id: str


@router.post("/select")
async def review_select(req: TopKRequest):
    """Submit top-K human selections.  Boosts those candidates' scores."""
    if app_state.review_service is None:
        raise HTTPException(status_code=400, detail="No active review session")
    from app.services.review_service import ReviewError
    try:
        app_state.review_service.submit_top_k(req.candidate_ids)
    except ReviewError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "selected": req.candidate_ids,
        "shortlist_count": len(app_state.review_service.get_shortlist()),
    }


@router.post("/pairwise")
async def review_pairwise(req: PairwiseRequest):
    """Submit a pairwise preference: winner > loser."""
    if app_state.review_service is None:
        raise HTTPException(status_code=400, detail="No active review session")
    from app.services.review_service import ReviewError
    try:
        app_state.review_service.submit_pairwise(req.winner_id, req.loser_id)
    except ReviewError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "winner": req.winner_id,
        "loser": req.loser_id,
        "history_count": len(app_state.review_service.get_pairwise_history()),
    }


@router.get("/shortlist")
async def review_shortlist():
    """Return the current human-selected shortlist."""
    if app_state.review_service is None:
        return {"shortlist": []}
    shortlist = app_state.review_service.get_shortlist()
    return {"shortlist": [c.candidate_id for c in shortlist]}
