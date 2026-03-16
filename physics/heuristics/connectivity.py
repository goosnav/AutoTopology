"""Connectivity checks — verify load paths exist from surfaces to ground.

Stage A check: ensures every functional surface has a connected path
to at least one ground anchor through support members.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx


@dataclass
class ConnectivityResult:
    """Result of connectivity analysis."""

    is_connected: bool
    surfaces_grounded: int
    surfaces_total: int
    failure_reasons: list[str]

    @property
    def score(self) -> float:
        """Fraction of surfaces with load paths to ground (0-1)."""
        if self.surfaces_total == 0:
            return 0.0
        return self.surfaces_grounded / self.surfaces_total


def check_connectivity(graph: nx.Graph) -> ConnectivityResult:
    """Check that all surface nodes have load paths to ground anchors.

    A surface is "grounded" if there exists any path through the graph
    from it to at least one ground_anchor node.
    """
    surfaces = [
        n for n, d in graph.nodes(data=True)
        if d.get("node_type") in ("surface", "head")
    ]
    ground_anchors = {
        n for n, d in graph.nodes(data=True)
        if d.get("node_type") == "ground_anchor"
    }

    if not surfaces:
        return ConnectivityResult(
            is_connected=False, surfaces_grounded=0,
            surfaces_total=0, failure_reasons=["No surface nodes found"],
        )

    if not ground_anchors:
        return ConnectivityResult(
            is_connected=False, surfaces_grounded=0,
            surfaces_total=len(surfaces),
            failure_reasons=["No ground anchor nodes found"],
        )

    failures: list[str] = []
    grounded = 0

    for surface in surfaces:
        has_path = any(
            nx.has_path(graph, surface, anchor)
            for anchor in ground_anchors
        )
        if has_path:
            grounded += 1
        else:
            failures.append(f"Surface '{surface}' has no load path to ground")

    return ConnectivityResult(
        is_connected=(grounded == len(surfaces)),
        surfaces_grounded=grounded,
        surfaces_total=len(surfaces),
        failure_reasons=failures,
    )
