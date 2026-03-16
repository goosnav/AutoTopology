# geometry/generators/chair_generator.py
"""Generate chair meshes from genomes."""

from __future__ import annotations

import math

import numpy as np
import trimesh

from core.genome.genome import Genome
from core.genome.chair_genes import CHAIR_GENE_CATALOG
from core.genome.graph_builder import build_graph
from geometry.primitives.primitives import make_box, make_cylinder, make_frustum, make_panel
from geometry.composition.assembler import assemble_meshes


def generate_chair_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a chair mesh from a genome."""
    g = genome.genes
    G = build_graph(genome, CHAIR_GENE_CATALOG)

    parts: list[trimesh.Trimesh] = []

    w, d = g["width"], g["depth"]
    seat_h = g["seat_height"]
    member_t = g["member_thickness"]
    taper = g["taper_ratio"]
    seat_thickness = max(member_t * 0.5, 15.0)

    # Seat
    seat = make_box(w, d, seat_thickness,
                    center=(0, 0, seat_h - seat_thickness / 2))
    parts.append(seat)

    # Legs and braces from graph
    for u, v, data in G.edges(data=True):
        if data["edge_type"] not in ("support_member", "brace_member"):
            continue
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        seg_len = float(np.linalg.norm(pos_u - pos_v))
        if seg_len < 1.0:
            continue

        center = tuple(((pos_u + pos_v) / 2).tolist())

        if data["edge_type"] == "support_member":
            r_bot = member_t / 2
            r_top = r_bot * taper
            part = make_frustum(r_bot, r_top, seg_len, center=center)
        else:
            part = make_cylinder(member_t / 4, seg_len, center=center)

        direction = pos_v - pos_u
        direction_norm = direction / np.linalg.norm(direction)
        z_axis = np.array([0, 0, 1])
        if not np.allclose(direction_norm, z_axis, atol=1e-6):
            axis = np.cross(z_axis, direction_norm)
            axis_len = np.linalg.norm(axis)
            if axis_len > 1e-8:
                axis = axis / axis_len
                angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                rot = trimesh.transformations.rotation_matrix(angle, axis, point=list(center))
                part.apply_transform(rot)

        parts.append(part)

    # Back panel
    back_top_node = G.nodes.get("back_top")
    back_base_node = G.nodes.get("back_base")
    if back_top_node and back_base_node:
        back_top_pos = np.array(back_top_node["pos"])
        back_base_pos = np.array(back_base_node["pos"])
        back_h = float(np.linalg.norm(back_top_pos - back_base_pos))
        if back_h > 1.0:
            center = tuple(((back_top_pos + back_base_pos) / 2).tolist())
            back = make_panel(w * 0.9, back_h, seat_thickness * 0.7, center=center)

            direction = back_top_pos - back_base_pos
            direction_norm = direction / np.linalg.norm(direction)
            z_axis = np.array([0, 0, 1])
            if not np.allclose(direction_norm, z_axis, atol=1e-6):
                axis = np.cross(z_axis, direction_norm)
                axis_len = np.linalg.norm(axis)
                if axis_len > 1e-8:
                    axis = axis / axis_len
                    angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                    rot = trimesh.transformations.rotation_matrix(angle, axis, point=list(center))
                    back.apply_transform(rot)

            parts.append(back)

    # Arm rests
    for side in ("left", "right"):
        arm_node = G.nodes.get(f"arm_{side}")
        if arm_node:
            arm_pos = arm_node["pos"]
            arm_len = d * 0.6
            arm = make_box(member_t, arm_len, member_t * 0.5,
                           center=(arm_pos[0], arm_pos[1], arm_pos[2]))
            parts.append(arm)

    return assemble_meshes(parts)
