"""AutoTopology developer CLI.

Provides subcommands for testing and debugging each subsystem independently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from app.__version__ import __version__

app = typer.Typer(
    name="autotopology-cli",
    help="AutoTopology developer CLI for testing and debugging subsystems.",
)


def _version_callback(value: bool):
    if value:
        typer.echo(f"AutoTopology v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", callback=_version_callback,
                                  is_eager=True, help="Show version"),
):
    """AutoTopology developer CLI."""
    pass


@app.command()
def validate_config(
    config: Path = typer.Option(
        Path("config/defaults/default_config.yaml"),
        "--config", "-c",
        help="Path to config YAML file",
    ),
):
    """Validate a configuration file."""
    from config.loader import load_config

    try:
        cfg = load_config(config)
        typer.echo(f"Config valid: {config}")
        typer.echo(f"  Families: {cfg.families.allowed_families}")
        typer.echo(f"  Population: {cfg.ea.population_count}")
        typer.echo(f"  Build volume: {cfg.geometry.build_volume.x}x{cfg.geometry.build_volume.y}x{cfg.geometry.build_volume.z}")
    except Exception as e:
        typer.echo(f"Config invalid: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def scan_models(
    models_dir: Path = typer.Option(
        Path("models"),
        "--models-dir", "-m",
        help="Path to models directory",
    ),
):
    """Scan for available VLM models."""
    from app.services.model_manager import scan_models as _scan, validate_models

    try:
        models = _scan(models_dir)
        if not models:
            typer.echo("No models found.")
            return
        for m in models:
            status = "OK" if m.compatible else f"INCOMPATIBLE: {m.errors}"
            size_mb = (m.base_size_bytes + m.mmproj_size_bytes) / (1024 * 1024)
            typer.echo(f"  {m.name}: {status} ({size_mb:.1f} MB)")
        compatible = [m for m in models if m.compatible]
        typer.echo(f"\n{len(compatible)}/{len(models)} models compatible")
    except Exception as e:
        typer.echo(f"Error scanning models: {e}", err=True)
        raise typer.Exit(code=1)


# --- Stubbed commands ---

def _stub(name: str):
    typer.echo(f"[{name}] Not implemented yet")
    raise typer.Exit(code=0)


@app.command()
def test_model_inference():
    """Test VLM inference with a sample image."""
    _stub("test-model-inference")


@app.command()
def generate_candidate_once(
    family: str = typer.Option("table_family", "--family", "-f"),
    seed: int = typer.Option(42, "--seed", "-s"),
    output_dir: Path = typer.Option(Path("."), "--output-dir", "-o"),
):
    """Generate a single candidate mesh and export as STL."""
    import random
    from core.genome.catalog_registry import get_catalog
    from core.genome.genome import Genome
    from geometry.generators.generator_registry import generate_mesh
    from geometry.mesh_validation.validator import validate_mesh
    from geometry.export.exporter import export_stl

    try:
        catalog = get_catalog(family)
        rng = random.Random(seed)
        genome = Genome.random_init(catalog, rng)
        mesh = generate_mesh(genome)
        report = validate_mesh(mesh)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        stl_path = output_dir / f"{genome.genome_id}.stl"
        json_path = output_dir / f"{genome.genome_id}.json"
        export_stl(mesh, stl_path, metadata=genome.to_dict(), metadata_path=json_path)

        typer.echo(f"Generated {family} candidate: {genome.genome_id}")
        typer.echo(f"  Mesh: {report}")
        typer.echo(f"  STL:  {stl_path}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def render_candidate_once(
    mesh: Optional[Path] = typer.Option(None, "--mesh"),
):
    """Render a candidate mesh to a 4-view collage."""
    _stub("render-candidate-once")


@app.command()
def evaluate_physics_once(
    family: str = typer.Option("table_family", "--family", "-f"),
    seed: int = typer.Option(42, "--seed", "-s"),
    material: str = typer.Option("wood", "--material", "-m"),
):
    """Evaluate physics heuristics for a generated candidate."""
    import random as _random
    from core.genome.catalog_registry import get_catalog
    from core.genome.genome import Genome
    from core.genome.graph_builder import build_graph
    from geometry.generators.generator_registry import generate_mesh
    from physics.scoring import evaluate_physics

    try:
        catalog = get_catalog(family)
        rng = _random.Random(seed)
        genome = Genome.random_init(catalog, rng)
        mesh = generate_mesh(genome)
        graph = build_graph(genome, catalog)
        result = evaluate_physics(mesh, graph, genome.genes, material_name=material)

        status = "PASS" if result.passed_hard_physics else "FAIL"
        typer.echo(f"Physics evaluation [{status}]: score={result.physics_score:.3f}")
        typer.echo(f"  Connectivity: {result.connectivity.score:.2f} (connected={result.connectivity.is_connected})")
        typer.echo(f"  Stability:    {result.stability.score:.2f} (stable={result.stability.is_stable})")
        typer.echo(f"  Thickness:    {result.thickness.score:.2f} (passed={result.thickness.passed})")
        typer.echo(f"  Beam:         {result.beam.score:.2f} (slenderness={result.beam.max_slenderness:.1f})")
        if result.failure_reasons:
            typer.echo(f"  Failures: {'; '.join(result.failure_reasons)}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def score_candidate_once(
    mesh: Optional[Path] = typer.Option(None, "--mesh"),
    model: str = typer.Option("moondream2", "--model"),
):
    """Score a candidate with VLM."""
    _stub("score-candidate-once")


@app.command()
def run_generation_once():
    """Run a single generation cycle."""
    _stub("run-generation-once")


@app.command()
def run_project(
    config: Path = typer.Option(Path("config/defaults/default_config.yaml"), "--config", "-c"),
):
    """Start a full evolution run."""
    _stub("run-project")


@app.command()
def resume_project(
    project_dir: Path = typer.Option(Path("."), "--project-dir"),
):
    """Resume an evolution run from checkpoint."""
    _stub("resume-project")


@app.command()
def export_candidate(
    candidate_id: str = typer.Argument(...),
):
    """Export a candidate's mesh and metadata."""
    _stub("export-candidate")


@app.command()
def cleanup_cache(
    project_dir: Path = typer.Option(Path("."), "--project-dir"),
):
    """Clean up transient cache files."""
    _stub("cleanup-cache")


@app.command()
def train_taste_model(
    project_dir: Path = typer.Option(Path("."), "--project-dir"),
):
    """Train the taste model from collected preferences."""
    _stub("train-taste-model")


@app.command()
def run_smoke_test():
    """Run a quick smoke test of all subsystems."""
    _stub("run-smoke-test")


if __name__ == "__main__":
    app()
