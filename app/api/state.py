"""Shared mutable state for the API layer.

Holds the singleton RunSession and associated services for the current run.
All endpoints access session state through this module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.services.export_service import ExportService
    from app.services.gallery_service import GalleryService
    from app.services.review_service import ReviewService
    from app.services.run_session import RunSession

# Singleton instances — set by run start / cleared by stop
run_session: Optional["RunSession"] = None
gallery_service: Optional["GalleryService"] = None
review_service: Optional["ReviewService"] = None
export_service: Optional["ExportService"] = None
