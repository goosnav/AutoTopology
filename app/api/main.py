"""FastAPI application shell."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.__version__ import __app_name__, __version__

app = FastAPI(
    title=__app_name__,
    version=__version__,
    description="Evolutionary furniture generator with AI aesthetic scoring",
)

# CORS for local browser UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static UI assets if directory exists
ui_assets_path = Path(__file__).parent.parent / "ui_assets"
if ui_assets_path.is_dir():
    app.mount("/static", StaticFiles(directory=str(ui_assets_path)), name="static")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": __version__,
        "app_name": __app_name__,
    }
