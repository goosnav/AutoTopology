#!/usr/bin/env python3
"""Cross-platform setup entry-point for AutoTopology.

Detects the current OS and delegates to the appropriate platform-specific
installer script.  Falls back to a generic Python-based setup if no
platform script exists.

Usage:
    python scripts/install/setup_all.py
    python scripts/install/setup_all.py --no-models
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
import venv
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

PLATFORM_SCRIPTS: dict[str, str] = {
    "Darwin": "setup_macos.sh",
    "Linux": "setup_linux.sh",
    "Windows": "setup_windows.ps1",
}

REQUIRED_DIRS = [
    "models/moondream2",
    "models/paddleocr-vl",
    "storage/checkpoints",
    "storage/cache",
    "storage/exports",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bold(text: str) -> str:
    """Wrap *text* in ANSI bold if stdout is a tty."""
    if sys.stdout.isatty():
        return f"\033[1m{text}\033[0m"
    return text


def _info(msg: str) -> None:
    print(f"[INFO]  {msg}")


def _ok(msg: str) -> None:
    print(f"[ OK ]  {msg}")


def _warn(msg: str) -> None:
    print(f"[WARN]  {msg}", file=sys.stderr)


def _fail(msg: str) -> None:
    print(f"[FAIL]  {msg}", file=sys.stderr)
    sys.exit(1)


def _check_python_version() -> None:
    """Abort if the running Python is below 3.11."""
    if sys.version_info < (3, 11):
        _fail(
            f"Python >= 3.11 required (running {platform.python_version()}). "
            "Please install a newer Python and re-run this script."
        )
    _ok(f"Python {platform.python_version()}")


def _run_platform_script(script_name: str, extra_args: list[str]) -> bool:
    """Run a platform-specific shell/ps1 script. Returns True on success."""
    script_path = SCRIPT_DIR / script_name

    if not script_path.exists():
        return False

    _info(f"Delegating to platform script: {script_path.name}")

    if script_name.endswith(".sh"):
        cmd = ["bash", str(script_path)] + extra_args
    elif script_name.endswith(".ps1"):
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)] + extra_args
    else:
        _warn(f"Don't know how to execute '{script_name}'. Falling back to generic setup.")
        return False

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        _fail(f"Platform script exited with code {result.returncode}.")
    return True


# ---------------------------------------------------------------------------
# Generic (fallback) setup – pure Python, works on any OS
# ---------------------------------------------------------------------------
def _generic_setup(*, skip_models: bool = False) -> None:
    """Perform a basic setup using only Python stdlib + pip."""
    print()
    print("=" * 60)
    print("  AutoTopology - Generic Python Setup")
    print("=" * 60)
    print()

    # 1. Python version
    _check_python_version()

    # 2. Virtual environment
    venv_dir = PROJECT_ROOT / "venv"
    if not venv_dir.exists():
        _info(f"Creating virtual environment at {venv_dir} ...")
        venv.create(str(venv_dir), with_pip=True)
        _ok("Virtual environment created.")
    else:
        _ok(f"Virtual environment already exists at {venv_dir}")

    # Determine venv python executable
    if sys.platform == "win32":
        venv_python = str(venv_dir / "Scripts" / "python.exe")
    else:
        venv_python = str(venv_dir / "bin" / "python3")

    if not Path(venv_python).exists():
        # Fallback for systems where python3 symlink isn't created
        alt = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / "python"
        if alt.exists():
            venv_python = str(alt)
        else:
            _fail(f"Cannot find Python executable in venv at {venv_dir}")

    # 3. Upgrade pip
    _info("Upgrading pip ...")
    subprocess.run(
        [venv_python, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        check=True,
    )

    # 4. Install project in editable mode with dev extras
    _info("Installing project dependencies (pip install -e '.[dev]') ...")
    subprocess.run(
        [venv_python, "-m", "pip", "install", "-e", f"{PROJECT_ROOT}[dev]", "--quiet"],
        check=True,
    )
    _ok("Dependencies installed.")

    # 5. Create required directories
    _info("Ensuring required directories exist ...")
    for rel in REQUIRED_DIRS:
        (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)
    _ok("Directories ready.")

    # 6. Optionally download models
    if not skip_models:
        _info("Downloading model files ...")
        download_script = SCRIPT_DIR / "download_models.py"
        result = subprocess.run(
            [venv_python, str(download_script), "--model-name", "moondream2"],
        )
        if result.returncode != 0:
            _warn("Model download failed. You can retry later:")
            _warn("    python scripts/install/download_models.py")
    else:
        _info("Skipping model download (--no-models).")

    # 7. Print summary
    activate_cmd = (
        r"venv\Scripts\activate" if sys.platform == "win32" else "source venv/bin/activate"
    )
    print()
    print("=" * 60)
    print(f"  {_bold('Setup complete!')}")
    print("=" * 60)
    print()
    print("  Next steps:")
    print()
    print(f"    1. Activate the environment:")
    print(f"         {activate_cmd}")
    print()
    print(f"    2. Run the test suite:")
    print(f"         pytest")
    print()
    print(f"    3. Download models (if skipped):")
    print(f"         python scripts/install/download_models.py")
    print()
    print(f"    4. Start the dev server:")
    print(f"         uvicorn app.api:app --reload")
    print()
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    extra_args = sys.argv[1:]
    skip_models = "--no-models" in extra_args

    system = platform.system()  # "Darwin", "Linux", "Windows"
    _info(f"Detected OS: {system} ({platform.platform()})")

    script_name = PLATFORM_SCRIPTS.get(system)

    if script_name:
        ran = _run_platform_script(script_name, extra_args)
        if ran:
            return  # platform script handled everything

        _warn(
            f"Platform script '{script_name}' not found. "
            "Falling back to generic Python setup."
        )

    # Fallback: generic pure-Python setup
    _generic_setup(skip_models=skip_models)


if __name__ == "__main__":
    main()
