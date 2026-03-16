"""Center-of-mass stability analysis.

Checks whether the center of mass projection falls within the support
polygon (convex hull of ground anchor positions). Uses a configurable
tolerance margin.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np
import trimesh


@dataclass
class StabilityResult:
    """Result of center-of-mass stability analysis."""

    is_stable: bool
    com: tuple[float, float, float]
    support_polygon_area: float
    com_distance_to_edge: float
    failure_reasons: list[str]

    @property
    def score(self) -> float:
        """Stability score (0-1) based on COM distance to support polygon edge.

        Higher is better — COM deep inside the polygon scores 1.0,
        COM near the edge scores lower, COM outside scores 0.
        """
        if not self.is_stable:
            return 0.0
        if self.support_polygon_area <= 0:
            return 0.0
        # Normalize by polygon "radius" (sqrt of area as rough reference)
        ref_radius = max(self.support_polygon_area ** 0.5, 1.0)
        return min(self.com_distance_to_edge / ref_radius, 1.0)


def check_stability(
    mesh: trimesh.Trimesh,
    graph: nx.Graph,
    tolerance: float = 0.0,
) -> StabilityResult:
    """Check if mesh COM projects inside the support polygon.

    Args:
        mesh: The candidate mesh.
        graph: Structural graph with ground_anchor nodes.
        tolerance: Margin in mm — COM can be this far outside polygon
            and still be considered stable.
    """
    com = mesh.center_mass
    if com is None or np.any(np.isnan(com)):
        return StabilityResult(
            is_stable=False, com=(0, 0, 0), support_polygon_area=0,
            com_distance_to_edge=0,
            failure_reasons=["Could not compute center of mass"],
        )

    com_tuple = (float(com[0]), float(com[1]), float(com[2]))

    # Collect ground anchor XY positions
    ground_xy = []
    for n, d in graph.nodes(data=True):
        if d.get("node_type") == "ground_anchor":
            pos = d["pos"]
            ground_xy.append([pos[0], pos[1]])

    if len(ground_xy) < 1:
        return StabilityResult(
            is_stable=False, com=com_tuple, support_polygon_area=0,
            com_distance_to_edge=0,
            failure_reasons=["No ground anchors for support polygon"],
        )

    ground_xy = np.array(ground_xy)

    # Single support: point stability check
    if len(ground_xy) == 1:
        dist = float(np.linalg.norm(com[:2] - ground_xy[0]))
        is_stable = dist <= tolerance
        return StabilityResult(
            is_stable=is_stable, com=com_tuple, support_polygon_area=0,
            com_distance_to_edge=-dist,
            failure_reasons=[] if is_stable else [
                f"COM is {dist:.1f}mm from single support point"
            ],
        )

    # Two supports: line stability check
    if len(ground_xy) == 2:
        p1, p2 = ground_xy[0], ground_xy[1]
        line_vec = p2 - p1
        line_len = np.linalg.norm(line_vec)
        if line_len < 1e-6:
            dist = float(np.linalg.norm(com[:2] - p1))
            is_stable = dist <= tolerance
            return StabilityResult(
                is_stable=is_stable, com=com_tuple, support_polygon_area=0,
                com_distance_to_edge=-dist,
                failure_reasons=[] if is_stable else [
                    f"COM is {dist:.1f}mm from collapsed support line"
                ],
            )
        # Distance from COM to the line segment
        t = np.clip(np.dot(com[:2] - p1, line_vec) / (line_len ** 2), 0, 1)
        closest = p1 + t * line_vec
        dist = float(np.linalg.norm(com[:2] - closest))
        is_stable = dist <= tolerance
        return StabilityResult(
            is_stable=is_stable, com=com_tuple, support_polygon_area=0,
            com_distance_to_edge=-dist if not is_stable else tolerance - dist,
            failure_reasons=[] if is_stable else [
                f"COM is {dist:.1f}mm from support line (tolerance={tolerance:.1f}mm)"
            ],
        )

    # 3+ supports: convex hull polygon check
    from shapely.geometry import MultiPoint, Point

    hull = MultiPoint(ground_xy.tolist()).convex_hull
    com_point = Point(com[0], com[1])
    polygon_area = float(hull.area)

    # Signed distance: positive means inside, negative means outside
    distance = float(hull.exterior.distance(com_point))
    is_inside = hull.contains(com_point) or hull.touches(com_point)

    if is_inside:
        signed_dist = distance
    else:
        signed_dist = -distance

    is_stable = signed_dist >= -tolerance

    return StabilityResult(
        is_stable=is_stable,
        com=com_tuple,
        support_polygon_area=polygon_area,
        com_distance_to_edge=signed_dist,
        failure_reasons=[] if is_stable else [
            f"COM projects {abs(signed_dist):.1f}mm outside support polygon"
        ],
    )
