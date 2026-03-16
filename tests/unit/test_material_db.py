"""Tests for physics/materials/material_db.py."""

import pytest

from physics.materials.material_db import get_material, MaterialProperties
from config.schemas.config_models import MaterialConfig


def test_get_preset_wood():
    mat = get_material("wood")
    assert mat.name == "wood"
    assert mat.density == 600
    assert mat.youngs_modulus == 12e9
    assert mat.slenderness_modifier == 1.0


def test_get_preset_steel():
    mat = get_material("steel")
    assert mat.name == "steel"
    assert mat.density == 7800


def test_get_all_presets():
    for name in ("wood", "plastic_printed", "aluminum", "steel", "stone_like"):
        mat = get_material(name)
        assert isinstance(mat, MaterialProperties)
        assert mat.density > 0
        assert mat.youngs_modulus > 0


def test_unknown_material_raises():
    with pytest.raises(ValueError, match="Unknown material"):
        get_material("unobtanium")


def test_override_takes_precedence():
    custom = MaterialConfig(
        name="wood", density=999, youngs_modulus=1e6,
        yield_strength=1e6, slenderness_modifier=2.0,
    )
    mat = get_material("wood", overrides={"wood": custom})
    assert mat.density == 999
    assert mat.slenderness_modifier == 2.0


def test_custom_material_via_override():
    custom = MaterialConfig(
        name="bamboo", density=400, youngs_modulus=15e9,
        yield_strength=50e6, slenderness_modifier=0.9,
    )
    mat = get_material("bamboo", overrides={"bamboo": custom})
    assert mat.name == "bamboo"
    assert mat.density == 400
