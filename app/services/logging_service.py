"""Logging service: dual-sink loguru configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from config.schemas.config_models import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Configure loguru with two sinks: rotating file + JSON-lines.

    Args:
        config: Logging configuration.
    """
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default sink
    logger.remove()

    # Console sink
    logger.add(
        sys.stderr,
        level=config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Human-readable rotating file
    logger.add(
        log_dir / "autotopology.log",
        level=config.log_level,
        rotation=f"{config.rotate_size_mb} MB",
        retention=f"{config.retention_days} days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    # Machine-readable JSON lines
    logger.add(
        log_dir / "autotopology.jsonl",
        level=config.log_level,
        rotation=f"{config.rotate_size_mb} MB",
        retention=f"{config.retention_days} days",
        serialize=True,
    )
