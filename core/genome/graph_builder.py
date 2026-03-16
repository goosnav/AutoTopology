"""Build a structural graph from a genome.

Each family produces a networkx.Graph with typed nodes (surface, ground_anchor,
head, etc.) and typed edges (support_member, brace_member, etc.). Node positions
are 3D coordinates in mm.
"""

from __future__ import annotations

import math

import networkx as nx

from core.genome.gene_types import GeneSpec
from core.genome.genome import Genome


def build_graph(genome: Genome, catalog: list[GeneSpec]) -> nx.Graph:
    """Dispatch to family-specific graph builder."""
    family = genome.genes.get("family_name")
    if family == "table_family":
        return _build_table_graph(genome)
    elif family == "lamp_family":
        return _build_lamp_graph(genome)
    elif family == "chair_family_lite":
        return _build_chair_graph(genome)
    raise ValueError(f"Unknown family: {family}")


def _build_table_graph(genome: Genome) -> nx.Graph:
    g = genome.genes
    G = nx.Graph()

    w, d, h = g["width"], g["depth"], g["height"]
    top_t = g["top_thickness"]
    n_supports = g["support_count"]
    inset = g["footprint_inset"]

    # Surface node (table top center)
    G.add_node("top", node_type="surface", pos=(0.0, 0.0, h))

    # Place supports based on strategy
    strategy = g["support_strategy"]
    support_positions = _place_supports(strategy, n_supports, w, d, inset)

    for i, (sx, sy) in enumerate(support_positions):
        node_id = f"leg_{i}"
        G.add_node(node_id, node_type="ground_anchor", pos=(sx, sy, 0.0))
        anchor_id = f"leg_top_{i}"
        G.add_node(anchor_id, node_type="surface_anchor", pos=(sx, sy, h - top_t))
        G.add_edge("top", anchor_id, edge_type="panel_attachment")
        G.add_edge(anchor_id, node_id, edge_type="support_member")

    # Braces between adjacent supports
    n_braces = min(g["brace_count"], len(support_positions))
    for i in range(n_braces):
        j = (i + 1) % len(support_positions)
        src = f"leg_{i}"
        dst = f"leg_{j}"
        brace_h = h * 0.3
        brace_id = f"brace_{i}"
        sx, sy, _ = G.nodes[src]["pos"]
        dx, dy, _ = G.nodes[dst]["pos"]
        mx, my = (sx + dx) / 2, (sy + dy) / 2
        G.add_node(brace_id, node_type="brace_point", pos=(mx, my, brace_h))
        G.add_edge(src, brace_id, edge_type="brace_member")
        G.add_edge(dst, brace_id, edge_type="brace_member")

    return G


def _build_lamp_graph(genome: Genome) -> nx.Graph:
    g = genome.genes
    G = nx.Graph()

    h = g["height"]
    stem_h = min(g["stem_height"], h * 0.9)
    n_supports = g["support_count"]
    w = g["width"]

    G.add_node("base", node_type="ground_anchor", pos=(0.0, 0.0, 0.0))
    G.add_node("stem_top", node_type="junction", pos=(0.0, 0.0, stem_h))
    G.add_edge("base", "stem_top", edge_type="support_member")

    G.add_node("head", node_type="head", pos=(0.0, 0.0, h))
    G.add_edge("stem_top", "head", edge_type="support_member")

    if n_supports > 1:
        angle_step = 2 * math.pi / n_supports
        base_r = w * 0.3
        for i in range(n_supports):
            angle = i * angle_step
            x = base_r * math.cos(angle)
            y = base_r * math.sin(angle)
            leg_id = f"foot_{i}"
            G.add_node(leg_id, node_type="ground_anchor", pos=(x, y, 0.0))
            G.add_edge(leg_id, "base", edge_type="brace_member")

    return G


def _build_chair_graph(genome: Genome) -> nx.Graph:
    g = genome.genes
    G = nx.Graph()

    w, d = g["width"], g["depth"]
    seat_h = g["seat_height"]
    n_supports = g["support_count"]
    has_back = g["back_present"]
    has_arms = g["arm_present"]
    back_h = g["back_height"]
    back_angle_deg = g["back_angle"]

    G.add_node("seat", node_type="surface", pos=(0.0, 0.0, seat_h))

    support_positions = _place_supports("corner", min(n_supports, 4), w, d, 0.05)
    for i, (sx, sy) in enumerate(support_positions):
        leg_id = f"leg_{i}"
        G.add_node(leg_id, node_type="ground_anchor", pos=(sx, sy, 0.0))
        anchor_id = f"leg_top_{i}"
        G.add_node(anchor_id, node_type="surface_anchor", pos=(sx, sy, seat_h))
        G.add_edge("seat", anchor_id, edge_type="panel_attachment")
        G.add_edge(anchor_id, leg_id, edge_type="support_member")

    if has_back:
        back_angle_rad = math.radians(back_angle_deg)
        back_top_y = -d / 2 - back_h * math.sin(back_angle_rad)
        back_top_z = seat_h + back_h * math.cos(back_angle_rad)
        G.add_node("back_top", node_type="back",
                    pos=(0.0, back_top_y, back_top_z))
        G.add_node("back_base", node_type="back_anchor",
                    pos=(0.0, -d / 2, seat_h))
        G.add_edge("seat", "back_base", edge_type="panel_attachment")
        G.add_edge("back_base", "back_top", edge_type="support_member")

    if has_arms:
        arm_h = seat_h + back_h * 0.5
        for side, x_sign in [("left", -1), ("right", 1)]:
            arm_id = f"arm_{side}"
            G.add_node(arm_id, node_type="arm",
                        pos=(x_sign * w / 2, 0.0, arm_h))
            G.add_edge("seat", arm_id, edge_type="panel_attachment")

    n_braces = min(g["brace_count"], len(support_positions))
    for i in range(n_braces):
        j = (i + 1) % len(support_positions)
        brace_id = f"brace_{i}"
        s_pos = G.nodes[f"leg_{i}"]["pos"]
        d_pos = G.nodes[f"leg_{j}"]["pos"]
        mx = (s_pos[0] + d_pos[0]) / 2
        my = (s_pos[1] + d_pos[1]) / 2
        G.add_node(brace_id, node_type="brace_point",
                    pos=(mx, my, seat_h * 0.3))
        G.add_edge(f"leg_{i}", brace_id, edge_type="brace_member")
        G.add_edge(f"leg_{j}", brace_id, edge_type="brace_member")

    return G


def _place_supports(
    strategy: str, count: int, width: float, depth: float, inset: float,
) -> list[tuple[float, float]]:
    """Compute 2D support positions based on strategy."""
    count = max(1, count)
    hw = width / 2 * (1 - inset)
    hd = depth / 2 * (1 - inset)

    if strategy == "pedestal" or count == 1:
        return [(0.0, 0.0)]

    if strategy in ("corner", "four_leg") and count >= 4:
        return [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)][:count]

    if strategy == "trestle" and count >= 2:
        return [(-hw, 0.0), (hw, 0.0)]

    positions = []
    for i in range(count):
        angle = 2 * math.pi * i / count
        x = hw * math.cos(angle)
        y = hd * math.sin(angle)
        positions.append((x, y))
    return positions
