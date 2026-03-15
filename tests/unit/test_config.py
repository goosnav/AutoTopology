"""Tests for config models and loader."""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from config.loader import load_config
from config.schemas.config_models import (
    BuildVolume,
    CacheConfig,
    EAConfig,
    ExportConfig,
    FamilyConfig,
    GeometryBounds,
    GeometryConfig,
    LoggingConfig,
    MaterialConfig,
    ProjectConfig,
    ScoringConfig,
    VLMConfig,
)
from core.exceptions import ConfigValidationError

FIXTURES = Path(__file__).parent.parent / "fixtures"


# --- BuildVolume ---

def test_build_volume_valid():
    bv = BuildVolume(x=300, y=300, z=400)
    assert bv.x == 300


def test_build_volume_rejects_negative():
    with pytest.raises(ValidationError):
        BuildVolume(x=-1, y=300, z=400)


def test_build_volume_rejects_zero():
    with pytest.raises(ValidationError):
        BuildVolume(x=0, y=300, z=400)


@given(
    x=st.floats(min_value=0.01, max_value=10000),
    y=st.floats(min_value=0.01, max_value=10000),
    z=st.floats(min_value=0.01, max_value=10000),
)
def test_build_volume_positive_always_valid(x, y, z):
    bv = BuildVolume(x=x, y=y, z=z)
    assert bv.x > 0 and bv.y > 0 and bv.z > 0


# --- MaterialConfig ---

def test_material_config_valid():
    m = MaterialConfig(name="wood", density=600, youngs_modulus=12e9, yield_strength=40e6)
    assert m.name == "wood"


def test_material_config_rejects_zero_density():
    with pytest.raises(ValidationError):
        MaterialConfig(name="bad", density=0, youngs_modulus=1e9, yield_strength=1e6)


def test_material_config_rejects_negative_modulus():
    with pytest.raises(ValidationError):
        MaterialConfig(name="bad", density=100, youngs_modulus=-1, yield_strength=1e6)


# --- FamilyConfig ---

def test_family_config_valid():
    fc = FamilyConfig(allowed_families=["table_family", "lamp_family"])
    assert len(fc.allowed_families) == 2


def test_family_config_rejects_unknown_family():
    with pytest.raises(ValidationError):
        FamilyConfig(allowed_families=["unknown_family"])


def test_family_config_rejects_empty():
    with pytest.raises(ValidationError):
        FamilyConfig(allowed_families=[])


# --- GeometryBounds ---

def test_geometry_bounds_valid():
    gb = GeometryBounds(min_width=100, max_width=2000, min_depth=100, max_depth=2000,
                        min_height=50, max_height=2500)
    assert gb.min_width < gb.max_width


def test_geometry_bounds_rejects_min_gt_max():
    with pytest.raises(ValidationError):
        GeometryBounds(min_width=2000, max_width=100)


def test_geometry_bounds_rejects_negative():
    with pytest.raises(ValidationError):
        GeometryBounds(min_width=-10, max_width=100)


# --- EAConfig ---

def test_ea_config_valid():
    ea = EAConfig(population_count=50)
    assert ea.population_count == 50


def test_ea_config_rejects_zero_population():
    with pytest.raises(ValidationError):
        EAConfig(population_count=0)


def test_ea_config_rejects_negative_population():
    with pytest.raises(ValidationError):
        EAConfig(population_count=-5)


def test_ea_config_rejects_zero_generations():
    with pytest.raises(ValidationError):
        EAConfig(review_every_n_generations=0)


# --- ScoringConfig ---

def test_scoring_config_valid():
    sc = ScoringConfig(aesthetic_weight=0.4, physics_weight=0.3, novelty_weight=0.2)
    assert sc.aesthetic_weight == 0.4


def test_scoring_config_rejects_all_zero_weights():
    with pytest.raises(ValidationError):
        ScoringConfig(aesthetic_weight=0, physics_weight=0, novelty_weight=0)


# --- VLMConfig ---

def test_vlm_config_defaults():
    vc = VLMConfig()
    assert vc.n_ctx == 512
    assert vc.fallback_mode == "physics_only"


def test_vlm_config_invalid_fallback():
    with pytest.raises(ValidationError):
        VLMConfig(fallback_mode="invalid")


# --- LoggingConfig ---

def test_logging_config_valid():
    lc = LoggingConfig(log_level="DEBUG")
    assert lc.log_level == "DEBUG"


def test_logging_config_normalizes_case():
    lc = LoggingConfig(log_level="info")
    assert lc.log_level == "INFO"


def test_logging_config_rejects_invalid_level():
    with pytest.raises(ValidationError):
        LoggingConfig(log_level="VERBOSE")


# --- ProjectConfig ---

def test_project_config_defaults():
    pc = ProjectConfig()
    assert pc.app.app_name == "AutoTopology"
    assert pc.ea.population_count == 50
    assert "table_family" in pc.families.allowed_families


def test_project_config_from_partial_dict():
    pc = ProjectConfig.model_validate({"ea": {"population_count": 100}})
    assert pc.ea.population_count == 100
    assert pc.app.app_name == "AutoTopology"  # default preserved


# --- Config Loader ---

def test_load_valid_config():
    config = load_config(FIXTURES / "valid_config.yaml")
    assert config.app.app_name == "TestTopology"
    assert "table_family" in config.families.allowed_families
    assert "lamp_family" in config.families.allowed_families


def test_load_default_config():
    config = load_config(Path(__file__).parent.parent.parent / "config" / "defaults" / "default_config.yaml")
    assert config.app.app_name == "AutoTopology"
    assert config.ea.population_count == 50


def test_load_missing_file():
    with pytest.raises(ConfigValidationError):
        load_config(Path("/nonexistent/config.yaml"))


def test_load_invalid_yaml(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("{{invalid yaml")
    with pytest.raises(ConfigValidationError):
        load_config(bad)


def test_load_config_with_negative_dims(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
geometry:
  build_volume:
    x: -100
    y: 300
    z: 400
""")
    with pytest.raises(ConfigValidationError):
        load_config(bad)


def test_load_config_with_zero_population(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
ea:
  population_count: 0
""")
    with pytest.raises(ConfigValidationError):
        load_config(bad)


def test_load_config_with_invalid_family(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
families:
  allowed_families:
    - sofa_family
""")
    with pytest.raises(ConfigValidationError):
        load_config(bad)


def test_load_config_min_gt_max(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
geometry:
  bounds:
    min_width: 2000
    max_width: 100
""")
    with pytest.raises(ConfigValidationError):
        load_config(bad)


def test_load_empty_yaml(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    config = load_config(empty)
    assert config.app.app_name == "AutoTopology"  # all defaults


def test_load_non_dict_yaml(tmp_path):
    bad = tmp_path / "list.yaml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(ConfigValidationError):
        load_config(bad)
