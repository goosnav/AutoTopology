# ProjectState.md — AutoTopology

**Last updated**: 2026-03-16
**Phase**: 2 (Geometry Core) — COMPLETE
**Test status**: 315/315 passing (~5s)

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python + C++ hybrid | Python for orchestration; C++ (pybind11) for batch EA ops (crossover, mutation, selection, novelty k-NN) |
| VLM strategy | Model-agnostic adapter | Any GGUF+mmproj pair dropped into `models/<subdir>/` auto-discovered |
| Primary VLM | Moondream2 (~1B params) | Purpose-built for image understanding, fits 16GB RAM. PaddleOCR-VL kept as secondary (OCR-focused, poor for aesthetics) |
| Mesh lifecycle | Transient — genomes persist, meshes regenerated on demand | Memory optimization for 16GB machines |
| Config | YAML + Pydantic v2 strict validation | `config/defaults/default_config.yaml` + `config/schemas/config_models.py` |
| API | FastAPI on localhost:8420 | Browser-based UI, WebSocket for live updates |
| Build | setuptools (pyproject.toml) | scikit-build-core planned for C++ integration |
| CLI | Typer with 14 subcommands | 3 functional (`validate-config`, `scan-models`, `generate-candidate-once`), 11 stubbed |
| C++ build | CMake + pybind11 | Minimal stub module (`autotopology_cpp`) builds and imports successfully |

## Completed Work

### Phase 1 (Foundations) — COMPLETE

| File | Status | Description |
|------|--------|-------------|
| `pyproject.toml` | Done | All deps, entry points, tool configs |
| `app/__version__.py` | Done | Version 0.1.0 |
| `core/exceptions.py` | Done | Base + 12 specific exception classes (spec S33.2) |
| `config/schemas/config_models.py` | Done | Full Pydantic v2 hierarchy: 10+ sub-models with validators |
| `config/loader.py` | Done | YAML -> Pydantic -> `ProjectConfig` or `ConfigValidationError` |
| `config/defaults/default_config.yaml` | Done | Complete defaults for table_family, 16GB Mac |
| `app/services/logging_service.py` | Done | Loguru dual-sink (rotating file + JSON-lines) |
| `app/services/model_manager.py` | Done | `ModelInfo`, `scan_models()`, `validate_models()`, `get_model_by_name()` |
| `storage/path_manager.py` | Done | `StorageManager`, `resolve_path()`, `sanitize_filename()` |
| `app/api/main.py` | Done | FastAPI app, CORS, `/health` endpoint |
| `run.py` | Done | Uvicorn launcher (port 8420) |
| `dev_cli.py` | Done | Typer CLI, 14 subcommands |
| `cpp/` | Done | CMake + pybind11 stub module |
| `scripts/install/` | Done | Model downloader, setup scripts |
| Directory scaffold | Done | ~40 Python packages with `__init__.py` |

### Phase 2 (Geometry Core) — COMPLETE

| File | Status | Description |
|------|--------|-------------|
| `core/genome/gene_types.py` | Done | `GeneSpec` dataclass with 4 gene types |
| `core/genome/genome.py` | Done | `Genome` class with `random_init()`, `validate()`, `clamp()`, serialization |
| `core/genome/table_genes.py` | Done | 26 genes across 4 layers |
| `core/genome/lamp_genes.py` | Done | Lamp family gene catalog |
| `core/genome/chair_genes.py` | Done | Chair family gene catalog |
| `core/genome/catalog_registry.py` | Done | `get_catalog()` auto-selects by family |
| `core/genome/graph_builder.py` | Done | Genome -> networkx.DiGraph |
| `geometry/primitives/primitives.py` | Done | `make_box()`, `make_cylinder()`, `make_frustum()` |
| `geometry/composition/assembler.py` | Done | Multi-primitive mesh assembly |
| `geometry/generators/table_generator.py` | Done | Table mesh generator |
| `geometry/generators/lamp_generator.py` | Done | Lamp mesh generator |
| `geometry/generators/chair_generator.py` | Done | Chair mesh generator |
| `geometry/generators/generator_registry.py` | Done | Family-based generator dispatch |
| `geometry/mesh_validation/validator.py` | Done | `MeshReport` + `validate_mesh()` |
| `geometry/export/exporter.py` | Done | STL export with JSON metadata |
| `app/api/routes.py` | Done | Root landing page + `/api/generate` endpoint |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | HTML landing page with project info and links |
| GET | `/health` | Health check (JSON) |
| GET | `/docs` | Swagger UI (auto-generated) |
| GET | `/api/generate` | Generate a candidate mesh (params: `family`, `seed`) |

## Test Coverage

| Test File | Tests | Covers |
|-----------|-------|--------|
| `tests/unit/test_exceptions.py` | 6 | Exception hierarchy, instantiation, inheritance |
| `tests/unit/test_config.py` | 36 | Config validation, defaults, ranges, hypothesis property tests |
| `tests/unit/test_services.py` | 20 | Logging, model manager, storage path manager |
| `tests/unit/test_cli.py` | 8 | CLI help, version, validate-config, scan-models, generate-candidate-once |
| `tests/unit/test_gene_types.py` | 11 | GeneSpec, GeneType enum |
| `tests/unit/test_genome.py` | 8 | Genome class |
| `tests/unit/test_family_catalogs.py` | 9 | Catalog registry, family catalogs |
| `tests/unit/test_graph_builder.py` | 8 | Graph conversion |
| `tests/unit/test_primitives.py` | 10 | Mesh primitive factories |
| `tests/unit/test_assembler.py` | 4 | Multi-primitive assembly |
| `tests/unit/test_table_generator.py` | 6 | Table mesh generation |
| `tests/unit/test_table_genes.py` | 9 | Table gene catalog |
| `tests/unit/test_lamp_chair_generators.py` | 10 | Lamp/Chair generators |
| `tests/unit/test_mesh_validator.py` | 6 | Mesh validation |
| `tests/unit/test_exporter.py` | 3 | STL export |
| `tests/unit/test_geometry_quality.py` | ~140 | Parametrized dimension matching |
| `tests/integration/test_api.py` | 4 | Health, root, generate endpoints |
| `tests/integration/test_geometry_batch.py` | 3 | Batch geometry validation |

## Known Issues & Fixes Applied

| Issue | Fix | Date |
|-------|-----|------|
| `sanitize_filename` regex | Changed test to assert absence of specific unsafe chars | 2026-03-15 |
| `GET /` returned 404 | Added router with root landing page + `/api/generate` endpoint | 2026-03-16 |
| `test_scan_models` fails without `models/` dir | Environment-dependent; requires `models/paddleocr-vl/` directory | Known |

## Open Tasks (by Phase)

### Phase 3A: Physics Heuristics (NEXT)
- [ ] `physics/materials/material_db.py` — Material database
- [ ] `physics/heuristics/connectivity.py` — Connectivity checks
- [ ] `physics/stability/com_analysis.py` — Center-of-mass stability
- [ ] `physics/heuristics/thickness.py` — Thickness gates
- [ ] `physics/beam/beam_model.py` — Beam approximation model

### Phase 3B: Rendering Pipeline (NEXT)
- [ ] `vision/collage/camera.py` — 4-view isometric camera setup
- [ ] `vision/collage/renderer.py` — Mesh rendering to images
- [ ] `vision/collage/collage.py` — 2x2 collage assembly

### Phase 4: VLM Scoring
- [ ] VLM loader (GGUF+mmproj), scoring prompts, response parser, score cache

### Phase 5: EA Core
- [ ] Candidate/Population/Island/League data structures, operators, fitness, migration

### Phase 6: UI & Review Loop
- [ ] API routes, WebSocket, gallery, review mode, browser frontend

### Phase 7: Taste Model (Optional)
- [ ] Pairwise ranking dataset, scikit-learn classifier, persistence

### Phase 8: Hardening
- [ ] Checkpointing, recovery, cache management, packaging, E2E smoke test

## Critical Path

```
Phase 1 (DONE) -> Phase 2 (DONE) -> Phase 3B -> Phase 4 -> Phase 5 -> Phase 6 -> Phase 8
                                 \-> Phase 3A --/                  \-> Phase 7 -/
```

## Environment Setup

```bash
# Quick start
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/                # 315 tests, all pass

# Run API server
python run.py               # localhost:8420 — landing page at /

# CLI
python dev_cli.py --help
python dev_cli.py validate-config
python dev_cli.py scan-models --models-dir models
python dev_cli.py generate-candidate-once --family table_family --seed 42
```
