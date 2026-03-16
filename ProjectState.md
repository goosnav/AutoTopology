# ProjectState.md — AutoTopology

**Last updated**: 2026-03-16
**Phase**: 3 (Physics & Rendering) — COMPLETE
**Test status**: 366/366 passing (~8s)

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python + C++ hybrid | Python for orchestration; C++ (pybind11) for batch EA ops |
| VLM strategy | Model-agnostic adapter | Any GGUF+mmproj pair dropped into `models/<subdir>/` auto-discovered |
| Primary VLM | Moondream2 (~1B params) | Purpose-built for image understanding, fits 16GB RAM |
| Mesh lifecycle | Transient — genomes persist, meshes regenerated on demand | Memory optimization for 16GB machines |
| Config | YAML + Pydantic v2 strict validation | `config/defaults/default_config.yaml` + `config/schemas/config_models.py` |
| API | FastAPI on localhost:8420 | Browser-based UI, WebSocket for live updates |
| CLI | Typer with 14 subcommands | 5 functional, 9 stubbed |
| Rendering | Multi-backend (pyrender > trimesh > wireframe fallback) | Always works regardless of GPU/display availability |
| Physics | Staged evaluation (A: cheap geometry, B: beam model) | Cheapest checks first, fail fast |

## Completed Phases

### Phase 1 (Foundations) — COMPLETE
Config, logging, API shell, CLI, exceptions, C++ stub, storage, model manager.

### Phase 2 (Geometry Core) — COMPLETE
Genomes (4 gene types, 3 family catalogs), graph builder, mesh primitives,
family-specific generators (table/lamp/chair), mesh validation, STL export,
`/api/generate` endpoint.

### Phase 3A (Physics Heuristics) — COMPLETE

| File | Description |
|------|-------------|
| `physics/materials/material_db.py` | Material lookup (5 presets + custom override) |
| `physics/heuristics/connectivity.py` | Graph connectivity: surfaces → ground anchors |
| `physics/stability/com_analysis.py` | Center-of-mass inside support polygon (Shapely) |
| `physics/heuristics/thickness.py` | Min thickness gate with material modifiers |
| `physics/beam/beam_model.py` | Slenderness ratios + deflection heuristics |
| `physics/scoring.py` | Orchestrator: PhysicsResult with gate + 0-1 score |

### Phase 3B (Rendering Pipeline) — COMPLETE

| File | Description |
|------|-------------|
| `vision/collage/camera.py` | 4-view isometric camera (deterministic transforms) |
| `vision/collage/renderer.py` | Multi-backend renderer with wireframe fallback |
| `vision/collage/collage.py` | 2x2 collage assembly + PNG save |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | HTML landing page |
| GET | `/health` | Health check (JSON) |
| GET | `/docs` | Swagger UI (auto-generated) |
| GET | `/api/generate` | Generate candidate (JSON: genome + mesh report) |
| GET | `/api/evaluate-physics` | Physics evaluation (JSON: scores + gate) |
| GET | `/api/render-collage` | 4-view collage (PNG image) |

## Functional CLI Commands

| Command | Description |
|---------|-------------|
| `validate-config` | Validate YAML config |
| `scan-models` | Scan for VLM models |
| `generate-candidate-once` | Generate mesh + STL |
| `evaluate-physics-once` | Run physics heuristics |
| `render-candidate-once` | Render 4-view collage PNG |

## Test Coverage

366 tests across 22 test files. Key areas:
- Config validation (36 tests, hypothesis property-based)
- Geometry quality (140+ parametrized dimension tests)
- Physics heuristics (36 tests across 6 modules)
- Rendering pipeline (17 tests: camera, wireframe, collage)
- API integration (4 endpoint tests)

## Known Issues

| Issue | Status |
|-------|--------|
| `test_scan_models` requires `models/` dir | Environment-dependent |
| PyOpenGL install fails in headless env | Wireframe fallback handles this |

## Open Tasks (by Phase)

### Phase 4: VLM Scoring (NEXT)
- [ ] `vision/adapters/vlm_loader.py` — GGUF+mmproj model loading
- [ ] `vision/prompts/scoring_prompt.py` — Structured scoring prompts
- [ ] `vision/parsers/response_parser.py` — JSON response extraction
- [ ] `vision/scoring/score_orchestrator.py` — Score cache + retry logic

### Phase 5: EA Core
- [ ] Candidate/Population/Island/League data structures
- [ ] Selection, crossover, mutation operators (Python + C++)
- [ ] Fitness composition, migration

### Phase 6: UI & Review Loop
- [ ] WebSocket for live updates, gallery, review mode, browser frontend

### Phase 7: Taste Model (Optional)
- [ ] Pairwise ranking, scikit-learn classifier, persistence

### Phase 8: Hardening
- [ ] Checkpointing, recovery, cache management, packaging

## Critical Path

```
Phase 1 (DONE) -> Phase 2 (DONE) -> Phase 3 (DONE) -> Phase 4 -> Phase 5 -> Phase 6 -> Phase 8
                                                                          \-> Phase 7 -/
```

## Environment Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/                # 366 tests
python run.py               # localhost:8420
python dev_cli.py --help
```
