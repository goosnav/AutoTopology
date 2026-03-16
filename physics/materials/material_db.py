"""Material database — lookup material properties by name.

Supports preset materials (wood, plastic_printed, aluminum, steel, stone_like)
and custom materials from config overrides.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.schemas.config_models import MaterialConfig, PRESET_MATERIALS


@dataclass
class MaterialProperties:
    """Resolved material properties for physics calculations."""

    name: str
    density: float  # kg/m^3
    youngs_modulus: float  # Pa
    yield_strength: float  # Pa
    slenderness_modifier: float


def get_material(
    name: str,
    overrides: dict[str, MaterialConfig] | None = None,
) -> MaterialProperties:
    """Look up material by name, checking overrides first, then presets."""
    if overrides and name in overrides:
        mc = overrides[name]
    elif name in PRESET_MATERIALS:
        mc = PRESET_MATERIALS[name]
    else:
        raise ValueError(
            f"Unknown material '{name}'. "
            f"Available: {sorted(set(PRESET_MATERIALS) | set(overrides or {}))}"
        )
    return MaterialProperties(
        name=mc.name,
        density=mc.density,
        youngs_modulus=mc.youngs_modulus,
        yield_strength=mc.yield_strength,
        slenderness_modifier=mc.slenderness_modifier,
    )
