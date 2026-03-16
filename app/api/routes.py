"""API routes for AutoTopology."""

from __future__ import annotations

import random
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, Response

from app.__version__ import __app_name__, __version__

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with project info and links."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{__app_name__}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a; color: #e0e0e0;
            display: flex; align-items: center; justify-content: center;
            min-height: 100vh;
        }}
        .container {{ max-width: 640px; padding: 2rem; text-align: center; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; color: #fff; }}
        .version {{ color: #888; margin-bottom: 2rem; }}
        .desc {{ color: #aaa; line-height: 1.6; margin-bottom: 2rem; }}
        .links {{ display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }}
        a {{
            display: inline-block; padding: 0.75rem 1.5rem;
            background: #1a1a2e; color: #64b5f6; text-decoration: none;
            border: 1px solid #333; border-radius: 8px;
            transition: background 0.2s;
        }}
        a:hover {{ background: #16213e; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{__app_name__}</h1>
        <p class="version">v{__version__}</p>
        <p class="desc">
            Evolutionary furniture generator with AI-powered aesthetic scoring.
            Generate, evolve, and refine 3D furniture designs using genetic algorithms
            and vision-language model evaluation.
        </p>
        <div class="links">
            <a href="/docs">API Docs</a>
            <a href="/health">Health Check</a>
            <a href="/api/generate">Generate</a>
            <a href="/api/evaluate-physics">Physics</a>
            <a href="/api/render-collage">Render</a>
        </div>
    </div>
</body>
</html>"""


@router.get("/api/generate")
async def generate_candidate(
    family: str = Query("table_family", description="Furniture family"),
    seed: Optional[int] = Query(None, description="Random seed (omit for random)"),
):
    """Generate a single candidate and return genome + mesh report."""
    from core.genome.catalog_registry import get_catalog
    from core.genome.genome import Genome
    from geometry.generators.generator_registry import generate_mesh
    from geometry.mesh_validation.validator import validate_mesh

    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    catalog = get_catalog(family)
    rng = random.Random(seed)
    genome = Genome.random_init(catalog, rng)
    mesh = generate_mesh(genome)
    report = validate_mesh(mesh)

    return {
        "genome_id": genome.genome_id,
        "family": family,
        "seed": seed,
        "mesh_report": {
            "vertex_count": report.vertex_count,
            "face_count": report.face_count,
            "volume": round(report.volume, 2),
            "is_watertight": report.is_watertight,
            "within_build_volume": report.within_build_volume,
            "is_acceptable": report.is_acceptable,
        },
        "genes": genome.to_dict()["genes"],
    }


@router.get("/api/evaluate-physics")
async def evaluate_physics_endpoint(
    family: str = Query("table_family", description="Furniture family"),
    seed: Optional[int] = Query(None, description="Random seed (omit for random)"),
    material: str = Query("wood", description="Material name"),
):
    """Generate a candidate and evaluate its physics properties."""
    from core.genome.catalog_registry import get_catalog
    from core.genome.genome import Genome
    from core.genome.graph_builder import build_graph
    from geometry.generators.generator_registry import generate_mesh
    from physics.scoring import evaluate_physics

    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    catalog = get_catalog(family)
    rng = random.Random(seed)
    genome = Genome.random_init(catalog, rng)
    mesh = generate_mesh(genome)
    graph = build_graph(genome, catalog)
    result = evaluate_physics(mesh, graph, genome.genes, material_name=material)

    return {
        "genome_id": genome.genome_id,
        "family": family,
        "seed": seed,
        "material": material,
        "passed_hard_physics": result.passed_hard_physics,
        "physics_score": result.physics_score,
        "sub_scores": result.sub_scores,
        "failure_reasons": result.failure_reasons,
    }


@router.get("/api/render-collage")
async def render_collage_endpoint(
    family: str = Query("table_family", description="Furniture family"),
    seed: Optional[int] = Query(None, description="Random seed (omit for random)"),
    resolution: int = Query(256, description="Resolution per view in pixels"),
):
    """Generate a candidate and return its 4-view collage as PNG."""
    from io import BytesIO
    from core.genome.catalog_registry import get_catalog
    from core.genome.genome import Genome
    from geometry.generators.generator_registry import generate_mesh
    from vision.collage.collage import render_collage

    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    catalog = get_catalog(family)
    rng = random.Random(seed)
    genome = Genome.random_init(catalog, rng)
    mesh = generate_mesh(genome)

    collage = render_collage(mesh, resolution_per_view=(resolution, resolution))

    buf = BytesIO()
    collage.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={"X-Genome-ID": genome.genome_id, "X-Seed": str(seed)},
    )
