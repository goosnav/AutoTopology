# AutoTopology

**Evolutionary furniture generator with AI-powered aesthetic scoring and human-in-the-loop design refinement.**

AutoTopology discovers novel furniture forms (tables, lamps, chairs) through evolutionary algorithms. A local vision-language model scores aesthetics, physics heuristics screen for structural plausibility, and periodic human review steers evolution toward your taste. The goal is form discovery and inspiration, not production CAD.

---

## How It Works

```
Define Constraints ──> Evolve Populations ──> AI Scores Aesthetics
       │                      │                      │
       │                      │                      v
       │                      │              Physics Screening
       │                      │                      │
       │                      v                      v
       │              Select Survivors ◄── Composite Fitness
       │                      │
       │              Every N generations
       │                      │
       v                      v
  YAML Config         Human Gallery Review
                              │
                              v
                     Export Top Designs (STL)
```

1. **Configure** — Define furniture type, dimensional bounds, material, and aesthetic preferences in YAML
2. **Evolve** — Multi-island EA with MAP-Elites diversity preservation generates populations of 3D forms
3. **Score** — Each candidate is rendered from 4 angles and scored by a local VLM on 7 aesthetic axes
4. **Screen** — Physics heuristics gate structurally implausible designs (stability, connectivity, member thickness)
5. **Review** — Periodically browse a gallery of top candidates, select favorites, compare pairs
6. **Export** — Download STL files + metadata for your favorite designs

## Key Features

- **Evolutionary Algorithm** — Islands + Leagues + MAP-Elites hybrid for maximum design diversity
- **Local AI Scoring** — Runs entirely on your machine via llama-cpp-python (no API keys, no cloud)
- **Model-Agnostic** — Drop any GGUF+mmproj model pair into `models/<name>/` and it auto-discovers
- **Human-in-the-Loop** — Your gallery picks train an optional taste model that biases future generations
- **Physics Aware** — Connectivity checks, center-of-mass stability, member slenderness limits
- **C++ Acceleration** — Performance-critical EA operations (crossover, mutation, selection, novelty) in C++ with Python fallbacks
- **Memory Conscious** — Designed for 16GB machines; meshes are transient, only genomes persist

## Requirements

- Python 3.11+
- macOS, Linux, or Windows
- 16GB RAM recommended
- ~2GB disk for VLM model files

## Quick Start

```bash
# Clone and setup
git clone https://github.com/your-org/AutoTopology.git
cd AutoTopology

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Download the recommended VLM (Moondream2, ~1B params)
python scripts/install/download_models.py

# Verify installation
pytest tests/
python dev_cli.py validate-config
python dev_cli.py scan-models --models-dir models
```

## Usage

### API Server

```bash
python run.py                      # Starts on http://localhost:8420
python run.py --port 9000          # Custom port
python run.py --reload             # Dev mode with auto-reload
```

### CLI

```bash
python dev_cli.py --help           # List all commands
python dev_cli.py validate-config  # Validate default config
python dev_cli.py validate-config --config my_config.yaml
python dev_cli.py scan-models --models-dir models
```

### Configuration

Edit `config/defaults/default_config.yaml` or provide your own:

```yaml
app:
  project_name: "my-table-project"

families:
  active_families:
    - table_family

geometry:
  build_volume:
    x_mm: 1500
    y_mm: 1000
    z_mm: 1200

ea:
  population_size: 50
  islands_per_league: 3
  leagues: 2
  review_interval_generations: 5
```

## Project Structure

```
AutoTopology/
├── app/                    # FastAPI application
│   ├── api/                #   Routes, WebSocket, health endpoint
│   ├── services/           #   Logging, model manager
│   ├── controllers/        #   Run state machine (planned)
│   ├── schemas/            #   API request/response models (planned)
│   └── ui_assets/          #   Browser frontend (planned)
├── core/                   # EA engine
│   ├── genome/             #   Gene specs, genome class, graph builder
│   ├── evolution/          #   Candidate, population, island, generation loop
│   ├── crossover/          #   Crossover operators
│   ├── mutation/           #   Mutation operators
│   ├── selection/          #   Tournament + mixed selection
│   ├── novelty/            #   k-NN novelty + archive
│   ├── map_elites/         #   MAP-Elites grid archive
│   ├── leagues/            #   Multi-league management
│   ├── repair/             #   Genome + mesh repair
│   └── exceptions.py       #   Exception hierarchy
├── geometry/               # 3D mesh generation
│   ├── generators/         #   Family-specific generators (table, lamp, chair)
│   ├── primitives/         #   Box, cylinder, frustum, panel
│   ├── composition/        #   Multi-primitive assembly
│   ├── mesh_validation/    #   Watertight, manifold, thickness checks
│   ├── footprints/         #   Support placement strategies
│   └── export/             #   STL export
├── physics/                # Structural plausibility
│   ├── materials/          #   Material property database
│   ├── heuristics/         #   Connectivity, stability, thickness, span
│   ├── beam/               #   Beam approximation model
│   ├── quick_fea/          #   Optional FEA for elites
│   └── stability/          #   Center-of-mass analysis
├── vision/                 # VLM integration
│   ├── adapters/           #   Model-agnostic VLM loader
│   ├── prompts/            #   Structured scoring prompts
│   ├── parsers/            #   JSON response parsing
│   ├── scoring/            #   Score orchestration + cache
│   └── collage/            #   4-view render + collage assembly
├── preference/             # Human taste learning
│   ├── ranking/            #   Pairwise comparison dataset + model
│   ├── features/           #   Feature extraction for taste model
│   └── persistence/        #   Model save/load
├── storage/                # Persistence
│   ├── checkpoints/        #   Atomic checkpoint save/load
│   ├── cache/              #   Transient file management
│   ├── db/                 #   SQLite score cache
│   ├── exports/            #   Final STL + metadata output
│   └── logs/               #   Rotating log files
├── config/                 # Configuration
│   ├── schemas/            #   Pydantic v2 model hierarchy
│   └── defaults/           #   Default YAML config
├── cpp/                    # C++ acceleration (pybind11)
│   ├── src/                #   Crossover, mutation, selection, novelty
│   ├── include/            #   Headers
│   ├── bindings.cpp        #   Python module definition
│   └── CMakeLists.txt      #   Build configuration
├── models/                 # VLM model files (gitignored)
│   ├── moondream2/         #   Recommended (~1B params)
│   └── paddleocr-vl/       #   Secondary option
├── scripts/
│   └── install/            #   Setup scripts, model downloader
├── tests/
│   ├── unit/               #   71 tests (config, exceptions, services, CLI)
│   ├── integration/        #   FastAPI endpoint tests
│   ├── e2e/                #   End-to-end smoke tests (planned)
│   └── fixtures/           #   Test config files
├── dev_cli.py              # Typer CLI entry point
├── run.py                  # Uvicorn launcher
├── pyproject.toml          # Project metadata + dependencies
└── CLAUDE.md               # Development workflow rules
```

## VLM Models

AutoTopology uses a local vision-language model to score candidate aesthetics. Models are stored in subdirectories under `models/` and auto-discovered at runtime.

**Recommended**: [Moondream2](https://huggingface.co/ggml-org/moondream2-20250414-GGUF) (~1B params, ~2GB) — purpose-built for image understanding, runs well on 16GB machines.

To add a new model, place its GGUF file and mmproj file in a new subdirectory:
```
models/my-model/
  my-model-text.gguf
  mmproj-my-model.gguf
```

The adapter identifies pairs by looking for "mmproj" in the filename.

## Development

```bash
# Run tests
pytest tests/
pytest tests/ -x --tb=short        # Stop on first failure

# Type checking
mypy app/ core/ config/ storage/

# Linting
ruff check .
ruff format .
```

## Spec & Plan

- Full specification: `AutoTopology_specs.txt` (1,719 lines, 43 sections)
- Implementation plan: `.claude/plans/enumerated-stargazing-map.md`
- Current status: `ProjectState.md`

## License

[To be determined]
