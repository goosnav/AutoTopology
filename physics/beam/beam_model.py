"""Beam approximation model — slenderness and deflection heuristics.

Stage B checks: approximate structural member behavior using simplified
beam theory. Produces slenderness scores and deflection estimates for
support members.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import networkx as nx

from physics.materials.material_db import MaterialProperties


# Slenderness ratio thresholds
SLENDERNESS_WARN = 15.0   # Warn above this
SLENDERNESS_HARD_FAIL = 30.0  # Hard fail above this

# Deflection limit: span / this ratio
DEFLECTION_LIMIT_RATIO = 200.0  # L/200 is common serviceability limit


@dataclass
class MemberAnalysis:
    """Analysis of a single structural member."""

    member_id: str
    length: float  # mm
    thickness: float  # mm
    slenderness_ratio: float
    estimated_deflection_mm: float
    span_deflection_ratio: float  # L/deflection


@dataclass
class BeamResult:
    """Result of beam approximation analysis."""

    passed: bool
    members: list[MemberAnalysis] = field(default_factory=list)
    max_slenderness: float = 0.0
    max_deflection_ratio: float = 0.0
    failure_reasons: list[str] = field(default_factory=list)

    @property
    def slenderness_score(self) -> float:
        """Score (0-1) based on worst slenderness ratio."""
        if self.max_slenderness <= 0:
            return 1.0
        if self.max_slenderness >= SLENDERNESS_HARD_FAIL:
            return 0.0
        if self.max_slenderness <= SLENDERNESS_WARN:
            return 1.0
        # Linear interpolation between warn and hard_fail
        t = (self.max_slenderness - SLENDERNESS_WARN) / (SLENDERNESS_HARD_FAIL - SLENDERNESS_WARN)
        return 1.0 - t

    @property
    def span_score(self) -> float:
        """Score (0-1) based on worst span/deflection ratio."""
        if not self.members:
            return 1.0
        worst = min(m.span_deflection_ratio for m in self.members) if self.members else float("inf")
        if worst >= DEFLECTION_LIMIT_RATIO:
            return 1.0
        if worst <= 0:
            return 0.0
        return min(worst / DEFLECTION_LIMIT_RATIO, 1.0)

    @property
    def score(self) -> float:
        """Combined beam score (0-1)."""
        return self.slenderness_score * 0.6 + self.span_score * 0.4


def analyze_beams(
    graph: nx.Graph,
    genome_genes: dict,
    material: MaterialProperties,
    load_per_member_n: float = 50.0,
) -> BeamResult:
    """Analyze structural members as simplified beams.

    Checks slenderness ratios and estimates deflection under load
    for support_member edges in the structural graph.

    Args:
        graph: Structural graph with typed edges and 3D node positions.
        genome_genes: Gene dict (for member_thickness, taper_ratio).
        material: Resolved material properties.
        load_per_member_n: Assumed load per member in Newtons.
    """
    member_t = genome_genes.get("member_thickness", 20.0)
    taper = genome_genes.get("taper_ratio", 1.0)
    stem_d = genome_genes.get("stem_diameter", 0)

    members: list[MemberAnalysis] = []
    failures: list[str] = []
    max_slenderness = 0.0

    for u, v, data in graph.edges(data=True):
        if data["edge_type"] not in ("support_member", "brace_member"):
            continue

        pos_u = np.array(graph.nodes[u]["pos"])
        pos_v = np.array(graph.nodes[v]["pos"])
        length = float(np.linalg.norm(pos_u - pos_v))

        if length < 1.0:
            continue

        # Determine cross-section diameter
        if data["edge_type"] == "brace_member":
            diameter = member_t / 2  # Braces are thinner
        elif stem_d > 0 and ("stem" in u or "stem" in v or "base" in u or "base" in v):
            diameter = stem_d
        else:
            # Average diameter accounting for taper
            diameter = member_t * (1 + taper) / 2

        # Apply material slenderness modifier
        effective_diameter = diameter * material.slenderness_modifier

        # Slenderness ratio: length / effective_diameter
        slenderness = length / effective_diameter if effective_diameter > 0 else float("inf")
        max_slenderness = max(max_slenderness, slenderness)

        # Estimate deflection using cantilever beam formula:
        # delta = P*L^3 / (3*E*I) where I = pi*d^4/64 for circular section
        # Convert mm to m for calculation, then back to mm
        L_m = length / 1000
        d_m = diameter / 1000
        I = math.pi * d_m ** 4 / 64  # Second moment of area (m^4)

        if I > 0 and material.youngs_modulus > 0:
            deflection_m = (load_per_member_n * L_m ** 3) / (3 * material.youngs_modulus * I)
            deflection_mm = deflection_m * 1000
        else:
            deflection_mm = float("inf")

        span_defl_ratio = length / deflection_mm if deflection_mm > 0 else float("inf")

        member_id = f"{u}->{v}"
        members.append(MemberAnalysis(
            member_id=member_id,
            length=length,
            thickness=diameter,
            slenderness_ratio=slenderness,
            estimated_deflection_mm=deflection_mm,
            span_deflection_ratio=span_defl_ratio,
        ))

        if slenderness > SLENDERNESS_HARD_FAIL:
            failures.append(
                f"Member {member_id}: slenderness {slenderness:.1f} > "
                f"hard limit {SLENDERNESS_HARD_FAIL}"
            )

    return BeamResult(
        passed=len(failures) == 0,
        members=members,
        max_slenderness=max_slenderness,
        failure_reasons=failures,
    )
