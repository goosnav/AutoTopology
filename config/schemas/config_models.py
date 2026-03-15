"""Pydantic v2 configuration models for AutoTopology.

All major run behavior is config-driven. This module defines the full
config hierarchy validated at load time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# --- Sub-models ---

class BuildVolume(BaseModel):
    """Printer build volume in mm."""
    x: float = Field(gt=0, description="Build volume X in mm")
    y: float = Field(gt=0, description="Build volume Y in mm")
    z: float = Field(gt=0, description="Build volume Z in mm")


class MaterialConfig(BaseModel):
    """Material properties for physics heuristics."""
    name: str
    density: float = Field(gt=0, description="kg/m^3")
    youngs_modulus: float = Field(gt=0, description="Pa (approximate)")
    yield_strength: float = Field(gt=0, description="Pa (approximate)")
    slenderness_modifier: float = Field(default=1.0, gt=0)


FamilyName = Literal["table_family", "lamp_family", "chair_family_lite"]


# --- Top-level config sections ---

class AppConfig(BaseModel):
    """Application-level settings."""
    app_name: str = "AutoTopology"
    project_root: Path = Field(default=Path("."))
    models_path: Path = Field(default=Path("models"))
    active_model: str = Field(default="moondream2", description="Subdirectory name under models_path")


class FamilyConfig(BaseModel):
    """Family selection settings."""
    allowed_families: list[FamilyName] = Field(
        default=["table_family"],
        min_length=1,
    )


class GeometryBounds(BaseModel):
    """Dimensional bounds for geometry generation (mm)."""
    min_width: float = Field(default=100.0, gt=0)
    max_width: float = Field(default=2000.0, gt=0)
    min_depth: float = Field(default=100.0, gt=0)
    max_depth: float = Field(default=2000.0, gt=0)
    min_height: float = Field(default=50.0, gt=0)
    max_height: float = Field(default=2500.0, gt=0)

    @model_validator(mode="after")
    def validate_min_max(self):
        if self.min_width > self.max_width:
            raise ValueError(f"min_width ({self.min_width}) > max_width ({self.max_width})")
        if self.min_depth > self.max_depth:
            raise ValueError(f"min_depth ({self.min_depth}) > max_depth ({self.max_depth})")
        if self.min_height > self.max_height:
            raise ValueError(f"min_height ({self.min_height}) > max_height ({self.max_height})")
        return self


class GeometryConfig(BaseModel):
    """Geometry generation settings."""
    build_volume: BuildVolume = Field(default_factory=lambda: BuildVolume(x=300, y=300, z=400))
    bounds: GeometryBounds = Field(default_factory=GeometryBounds)
    material_default: str = "wood"
    material_overrides: dict[str, MaterialConfig] = Field(default_factory=dict)


PRESET_MATERIALS: dict[str, MaterialConfig] = {
    "wood": MaterialConfig(
        name="wood", density=600, youngs_modulus=12e9,
        yield_strength=40e6, slenderness_modifier=1.0,
    ),
    "plastic_printed": MaterialConfig(
        name="plastic_printed", density=1200, youngs_modulus=2.5e9,
        yield_strength=50e6, slenderness_modifier=0.8,
    ),
    "aluminum": MaterialConfig(
        name="aluminum", density=2700, youngs_modulus=69e9,
        yield_strength=270e6, slenderness_modifier=1.2,
    ),
    "steel": MaterialConfig(
        name="steel", density=7800, youngs_modulus=200e9,
        yield_strength=250e6, slenderness_modifier=1.5,
    ),
    "stone_like": MaterialConfig(
        name="stone_like", density=2500, youngs_modulus=30e9,
        yield_strength=10e6, slenderness_modifier=0.6,
    ),
}


class EAConfig(BaseModel):
    """Evolutionary algorithm settings."""
    population_count: int = Field(default=50, gt=0)
    islands_per_league: int = Field(default=3, gt=0)
    league_count: int = Field(default=2, gt=0)
    candidates_per_generation: int = Field(default=20, gt=0)
    review_every_n_generations: int = Field(default=5, gt=0)
    top_k_selection_count: int = Field(default=5, gt=0)
    pairwise_tiebreak_count: int = Field(default=3, ge=0)
    migration_rate: float = Field(default=0.1, ge=0, le=1)
    migration_interval: int = Field(default=3, gt=0)
    tournament_size: int = Field(default=3, gt=0)
    mutation_rate: float = Field(default=0.3, gt=0, le=1)
    crossover_rate: float = Field(default=0.7, gt=0, le=1)


class ScoringConfig(BaseModel):
    """Fitness scoring weights and thresholds."""
    physics_gate_threshold: float = Field(default=0.3, ge=0, le=1)
    aesthetic_weight: float = Field(default=0.4, ge=0)
    physics_weight: float = Field(default=0.3, ge=0)
    novelty_weight: float = Field(default=0.2, ge=0)
    taste_weight: float = Field(default=0.1, ge=0)

    @model_validator(mode="after")
    def validate_weights_positive_sum(self):
        total = self.aesthetic_weight + self.physics_weight + self.novelty_weight
        if total <= 0:
            raise ValueError("Sum of core scoring weights must be positive")
        return self


class VLMConfig(BaseModel):
    """Vision language model inference settings."""
    n_ctx: int = Field(default=512, gt=0)
    n_gpu_layers: int = Field(default=0, ge=0)
    temperature: float = Field(default=0.1, ge=0, le=2)
    max_retries: int = Field(default=2, ge=0)
    failure_rate_threshold: float = Field(default=0.5, gt=0, le=1)
    fallback_mode: Literal["fail", "physics_only", "cached"] = "physics_only"


class TasteConfig(BaseModel):
    """Optional taste model settings."""
    enabled: bool = False
    model_type: str = "logistic_regression"
    retrain_every_n_reviews: int = Field(default=1, gt=0)


class CacheConfig(BaseModel):
    """Cache retention settings."""
    keep_last_n_generations: int = Field(default=3, gt=0)
    max_cache_size_mb: int = Field(default=2000, gt=0)


class ExportConfig(BaseModel):
    """Export settings."""
    export_top_n_on_stop: int = Field(default=10, gt=0)
    formats: list[Literal["stl", "obj", "glb"]] = Field(default=["stl"])
    include_metadata: bool = True
    include_collage: bool = True


class LoggingConfig(BaseModel):
    """Logging settings."""
    log_level: str = Field(default="INFO")
    log_dir: Path = Field(default=Path("storage/logs"))
    rotate_size_mb: int = Field(default=10, gt=0)
    retention_days: int = Field(default=30, gt=0)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return v.upper()


# --- Root config ---

class ProjectConfig(BaseModel):
    """Root configuration composing all sub-configs."""
    app: AppConfig = Field(default_factory=AppConfig)
    families: FamilyConfig = Field(default_factory=FamilyConfig)
    geometry: GeometryConfig = Field(default_factory=GeometryConfig)
    ea: EAConfig = Field(default_factory=EAConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    vlm: VLMConfig = Field(default_factory=VLMConfig)
    taste: TasteConfig = Field(default_factory=TasteConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
