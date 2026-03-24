"""Export endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api import state as app_state

router = APIRouter(prefix="/api", tags=["export"])


@router.post("/export/{candidate_id}")
async def export_candidate(candidate_id: str):
    """Export a candidate's metadata (and STL if mesh available)."""
    if app_state.gallery_service is None:
        raise HTTPException(status_code=404, detail="No active gallery")

    c = app_state.gallery_service.get_by_id(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")

    if app_state.export_service is None:
        raise HTTPException(status_code=500, detail="Export service not initialised")

    result = app_state.export_service.export(c)
    return result
