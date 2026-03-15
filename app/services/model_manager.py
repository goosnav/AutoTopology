"""Model manager: discover and validate GGUF+MMProj pairs in model subdirectories."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.exceptions import ModelDiscoveryError


@dataclass
class ModelInfo:
    """Information about a discovered VLM model pair."""
    name: str
    base_path: Path
    mmproj_path: Path
    base_size_bytes: int = 0
    mmproj_size_bytes: int = 0
    compatible: bool = True
    errors: list[str] = field(default_factory=list)


def scan_models(models_path: Path) -> list[ModelInfo]:
    """Scan subdirectories under models_path for GGUF+MMProj pairs.

    Each subdirectory is treated as a model. Within each subdir:
    - Files with 'mmproj' in the name are projector files
    - Other .gguf files are base model files

    Args:
        models_path: Root models directory.

    Returns:
        List of discovered ModelInfo.

    Raises:
        ModelDiscoveryError: If models_path doesn't exist or is not a directory.
    """
    if not models_path.exists():
        raise ModelDiscoveryError(
            f"Models directory not found: {models_path}",
            details={"path": str(models_path)},
        )
    if not models_path.is_dir():
        raise ModelDiscoveryError(
            f"Models path is not a directory: {models_path}",
            details={"path": str(models_path)},
        )

    models = []
    for subdir in sorted(models_path.iterdir()):
        if not subdir.is_dir():
            continue

        gguf_files = list(subdir.glob("*.gguf"))
        if not gguf_files:
            continue

        mmproj_files = [f for f in gguf_files if "mmproj" in f.name.lower()]
        base_files = [f for f in gguf_files if "mmproj" not in f.name.lower()]

        errors = []
        if not base_files:
            errors.append("No base model GGUF found")
        if not mmproj_files:
            errors.append("No mmproj GGUF found")

        info = ModelInfo(
            name=subdir.name,
            base_path=base_files[0] if base_files else Path(),
            mmproj_path=mmproj_files[0] if mmproj_files else Path(),
            base_size_bytes=base_files[0].stat().st_size if base_files else 0,
            mmproj_size_bytes=mmproj_files[0].stat().st_size if mmproj_files else 0,
            compatible=len(errors) == 0,
            errors=errors,
        )
        models.append(info)

    return models


def validate_models(models: list[ModelInfo]) -> list[ModelInfo]:
    """Filter to compatible models and raise if none found.

    Args:
        models: List from scan_models.

    Returns:
        List of compatible models.

    Raises:
        ModelDiscoveryError: If no compatible models found.
    """
    compatible = [m for m in models if m.compatible]
    if not compatible:
        all_errors = {m.name: m.errors for m in models}
        raise ModelDiscoveryError(
            "No compatible VLM models found",
            details={"scanned_models": all_errors},
        )
    return compatible


def get_model_by_name(models: list[ModelInfo], name: str) -> ModelInfo:
    """Get a specific model by name.

    Args:
        models: List of models.
        name: Model subdirectory name.

    Returns:
        Matching ModelInfo.

    Raises:
        ModelDiscoveryError: If model not found.
    """
    for m in models:
        if m.name == name:
            if not m.compatible:
                raise ModelDiscoveryError(
                    f"Model '{name}' found but not compatible: {m.errors}",
                    details={"model": name, "errors": m.errors},
                )
            return m
    available = [m.name for m in models]
    raise ModelDiscoveryError(
        f"Model '{name}' not found. Available: {available}",
        details={"requested": name, "available": available},
    )
