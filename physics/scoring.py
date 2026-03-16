"""Physics scoring orchestrator — runs staged evaluation pipeline.

Stage A (cheap): connectivity, stability, thickness
Stage B (moderate): beam approximation

Produces PhysicsResult with both a hard gate boolean and a 0-1 score.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx
import trimesh

from physics.heuristics.connectivity import ConnectivityResult, check_connectivity
from physics.stability.com_analysis import StabilityResult, check_stability
from physics.heuristics.thickness import ThicknessResult, check_thickness
from physics.beam.beam_model import BeamResult, analyze_beams
from physics.materials.material_db import MaterialProperties, get_material


@dataclass
class PhysicsResult:
    """Complete physics evaluation result for a candidate."""

    passed_hard_physics: bool
    physics_score: float
    connectivity: ConnectivityResult
    stability: StabilityResult
    thickness: ThicknessResult
    beam: BeamResult
    failure_reasons: list[str] = field(default_factory=list)

    @property
    def sub_scores(self) -> dict[str, float]:
        return {
            "connectivity_score": self.connectivity.score,
            "stability_score": self.stability.score,
            "thickness_score": self.thickness.score,
            "slenderness_score": self.beam.slenderness_score,
            "span_score": self.beam.span_score,
            "beam_score": self.beam.score,
        }


def evaluate_physics(
    mesh: trimesh.Trimesh,
    graph: nx.Graph,
    genome_genes: dict,
    material_name: str = "wood",
    material_overrides: dict | None = None,
    physics_gate_threshold: float = 0.3,
    stability_tolerance_mm: float = 10.0,
) -> PhysicsResult:
    """Run the full physics evaluation pipeline.

    Args:
        mesh: Candidate mesh.
        graph: Structural graph from graph_builder.
        genome_genes: Raw gene dictionary.
        material_name: Material to use for properties lookup.
        material_overrides: Optional config overrides for materials.
        physics_gate_threshold: Score below this = hard fail.
        stability_tolerance_mm: How far COM can be outside support polygon.

    Returns:
        PhysicsResult with gate decision and normalized score.
    """
    material = get_material(material_name, material_overrides)

    # Stage A: Cheap geometry checks
    connectivity = check_connectivity(graph)
    stability = check_stability(mesh, graph, tolerance=stability_tolerance_mm)
    thickness = check_thickness(graph, genome_genes, material)

    # Stage B: Beam approximation
    beam = analyze_beams(graph, genome_genes, material)

    # Aggregate failures
    all_failures = (
        connectivity.failure_reasons
        + stability.failure_reasons
        + thickness.failure_reasons
        + beam.failure_reasons
    )

    # Compute weighted physics score
    score = (
        connectivity.score * 0.3
        + stability.score * 0.3
        + thickness.score * 0.2
        + beam.score * 0.2
    )

    # Hard physics gate: connectivity failure or score below threshold
    hard_fail = (
        not connectivity.is_connected
        or not stability.is_stable
        or score < physics_gate_threshold
    )

    return PhysicsResult(
        passed_hard_physics=not hard_fail,
        physics_score=round(score, 4),
        connectivity=connectivity,
        stability=stability,
        thickness=thickness,
        beam=beam,
        failure_reasons=all_failures,
    )
