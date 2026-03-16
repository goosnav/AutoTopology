"""Thickness gate — check that support members meet minimum thickness.

Stage A check: verifies primary support members (legs, stems) are not
below configured minimum thickness, adjusted by material slenderness modifier.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import networkx as nx

from physics.materials.material_db import MaterialProperties


# Default minimum thickness for support members (mm)
DEFAULT_MIN_THICKNESS_MM = 8.0


@dataclass
class ThicknessResult:
    """Result of thickness gate checks."""

    passed: bool
    min_thickness_found: float
    min_thickness_required: float
    thin_members: list[str]
    failure_reasons: list[str]

    @property
    def score(self) -> float:
        """Thickness score (0-1). 1.0 if all members pass, degrades linearly."""
        if self.min_thickness_required <= 0:
            return 1.0
        ratio = self.min_thickness_found / self.min_thickness_required
        return min(max(ratio, 0.0), 1.0)


def check_thickness(
    graph: nx.Graph,
    genome_genes: dict,
    material: MaterialProperties,
    min_thickness_mm: float = DEFAULT_MIN_THICKNESS_MM,
) -> ThicknessResult:
    """Check support member thicknesses against minimum requirements.

    The minimum thickness is adjusted by material slenderness modifier:
    effective_min = min_thickness_mm / slenderness_modifier

    Args:
        graph: Structural graph with typed edges.
        genome_genes: Gene dict containing member_thickness, top_thickness, etc.
        material: Resolved material properties.
        min_thickness_mm: Base minimum thickness in mm.
    """
    effective_min = min_thickness_mm / material.slenderness_modifier

    thin_members: list[str] = []
    failures: list[str] = []
    min_found = float("inf")

    # Check member_thickness (legs, supports)
    member_t = genome_genes.get("member_thickness", 0)
    if member_t < effective_min:
        thin_members.append(f"support_members ({member_t:.1f}mm)")
        failures.append(
            f"Support member thickness {member_t:.1f}mm < min {effective_min:.1f}mm"
        )
    min_found = min(min_found, member_t) if member_t > 0 else min_found

    # Check top_thickness (table top, seat)
    top_t = genome_genes.get("top_thickness", 0)
    if top_t > 0:
        top_min = effective_min * 0.5  # Surface panels can be thinner
        if top_t < top_min:
            thin_members.append(f"top_surface ({top_t:.1f}mm)")
            failures.append(
                f"Surface thickness {top_t:.1f}mm < min {top_min:.1f}mm"
            )
        min_found = min(min_found, top_t)

    # Check stem_diameter for lamp family
    stem_d = genome_genes.get("stem_diameter", 0)
    if stem_d > 0:
        if stem_d < effective_min:
            thin_members.append(f"stem ({stem_d:.1f}mm)")
            failures.append(
                f"Stem diameter {stem_d:.1f}mm < min {effective_min:.1f}mm"
            )
        min_found = min(min_found, stem_d)

    if min_found == float("inf"):
        min_found = 0.0

    return ThicknessResult(
        passed=len(failures) == 0,
        min_thickness_found=min_found,
        min_thickness_required=effective_min,
        thin_members=thin_members,
        failure_reasons=failures,
    )
