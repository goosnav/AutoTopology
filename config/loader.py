"""Config loader: YAML -> Pydantic validation -> ProjectConfig."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from config.schemas.config_models import ProjectConfig
from core.exceptions import ConfigValidationError


def load_config(path: Path) -> ProjectConfig:
    """Load and validate a YAML config file.

    Args:
        path: Path to YAML config file.

    Returns:
        Validated ProjectConfig.

    Raises:
        ConfigValidationError: If file missing, unparseable, or fails validation.
    """
    if not path.exists():
        raise ConfigValidationError(
            f"Config file not found: {path}",
            details={"path": str(path)},
        )

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigValidationError(
            f"Cannot read config file: {e}",
            details={"path": str(path)},
        ) from e

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ConfigValidationError(
            f"Invalid YAML: {e}",
            details={"path": str(path)},
        ) from e

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ConfigValidationError(
            f"Config must be a YAML mapping, got {type(data).__name__}",
            details={"path": str(path)},
        )

    try:
        return ProjectConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigValidationError(
            f"Config validation failed: {e}",
            details={"path": str(path), "errors": e.errors()},
        ) from e
