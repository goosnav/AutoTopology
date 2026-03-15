#!/usr/bin/env bash
# setup_macos.sh – Bootstrap AutoTopology dev environment on macOS.
#
# Usage:
#     bash scripts/install/setup_macos.sh           # full setup
#     bash scripts/install/setup_macos.sh --no-models  # skip model download
set -euo pipefail

# ── Resolve project root (two levels up from this script) ─────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Colours ───────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

SKIP_MODELS=false
for arg in "$@"; do
    case "$arg" in
        --no-models) SKIP_MODELS=true ;;
        *) warn "Unknown argument: $arg" ;;
    esac
done

echo ""
echo "============================================================"
echo "  AutoTopology – macOS Setup"
echo "============================================================"
echo ""

# ── 1. Check Python version ──────────────────────────────────────────────
info "Checking Python version ..."

PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    fail "Python 3 not found. Install Python 3.11+ from https://python.org or via Homebrew:\n    brew install python@3.12"
fi

PY_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$("$PYTHON" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    fail "Python >= 3.11 is required (found $PY_VERSION). Install a newer version:\n    brew install python@3.12"
fi

ok "Python $PY_VERSION ($PYTHON)"

# ── 2. Create / activate venv ────────────────────────────────────────────
VENV_DIR="$PROJECT_ROOT/venv"

if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment at $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
    ok "Virtual environment created."
else
    ok "Virtual environment already exists at $VENV_DIR"
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
ok "Activated venv ($(python3 --version))"

# ── 3. Upgrade pip & install dependencies ────────────────────────────────
info "Upgrading pip ..."
python3 -m pip install --upgrade pip --quiet

info "Installing project dependencies (pip install -e '.[dev]') ..."
python3 -m pip install -e "${PROJECT_ROOT}[dev]" --quiet
ok "Dependencies installed."

# ── 4. Create required directories ───────────────────────────────────────
info "Ensuring required directories exist ..."
DIRS=(
    "$PROJECT_ROOT/models/moondream2"
    "$PROJECT_ROOT/models/paddleocr-vl"
    "$PROJECT_ROOT/storage/checkpoints"
    "$PROJECT_ROOT/storage/cache"
    "$PROJECT_ROOT/storage/exports"
)
for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
done
ok "Directories ready."

# ── 5. Optionally download models ────────────────────────────────────────
if [ "$SKIP_MODELS" = false ]; then
    echo ""
    info "Downloading model files (this may take a while) ..."
    python3 "$SCRIPT_DIR/download_models.py" --model-name moondream2 || {
        warn "Model download failed – you can retry later with:"
        warn "    python scripts/install/download_models.py"
    }
else
    info "Skipping model download (--no-models)."
fi

# ── 6. Summary / next steps ──────────────────────────────────────────────
echo ""
echo "============================================================"
echo -e "  ${GREEN}Setup complete!${NC}"
echo "============================================================"
echo ""
echo "  Next steps:"
echo ""
echo "    1. Activate the environment:"
echo "         source venv/bin/activate"
echo ""
echo "    2. Run the test suite:"
echo "         pytest"
echo ""
echo "    3. Download models (if skipped):"
echo "         python scripts/install/download_models.py"
echo ""
echo "    4. Start the dev server:"
echo "         uvicorn app.api:app --reload"
echo ""
echo "============================================================"
