# geometry/generators/table_generator.py
"""Generate table meshes from genomes."""

from __future__ import annotations

import math

import numpy as np
import trimesh

from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from core.genome.graph_builder import build_graph
from geometry.primitives.primitives import make_box, make_cylinder, make_frustum
from geometry.composition.assembler import assemble_meshes


def generate_table_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a table mesh from a genome."""
    g = genome.genes
    G = build_graph(genome, TABLE_GENE_CATALOG)

    parts: list[trimesh.Trimesh] = []

    w, d, h = g["width"], g["depth"], g["height"]
    top_t = g["top_thickness"]
    member_t = g["member_thickness"]
    taper = g["taper_ratio"]

    # Table top
    top = make_box(w, d, top_t, center=(0, 0, h - top_t / 2))
    parts.append(top)

    # Legs: edges of type "support_member"
    for u, v, data in G.edges(data=True):
        if data["edge_type"] != "support_member":
            continue
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        if pos_u[2] > pos_v[2]:
            top_pos, bot_pos = pos_u, pos_v
        else:
            top_pos, bot_pos = pos_v, pos_u

        leg_h = float(np.linalg.norm(top_pos - bot_pos))
        if leg_h < 1.0:
            continue

        center = ((top_pos + bot_pos) / 2).tolist()
        r_bot = member_t / 2
        r_top = r_bot * taper

        leg = make_frustum(r_bot, r_top, leg_h, center=tuple(center))

        direction = top_pos - bot_pos
        direction_norm = direction / np.linalg.norm(direction)
        z_axis = np.array([0, 0, 1])

        if not np.allclose(direction_norm, z_axis, atol=1e-6):
            axis = np.cross(z_axis, direction_norm)
            axis_len = np.linalg.norm(axis)
            if axis_len > 1e-8:
                axis = axis / axis_len
                angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                rot = trimesh.transformations.rotation_matrix(angle, axis, point=center)
                leg.apply_transform(rot)

        parts.append(leg)

    # Braces
    for u, v, data in G.edges(data=True):
        if data["edge_type"] != "brace_member":
            continue
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        brace_len = float(np.linalg.norm(pos_u - pos_v))
        if brace_len < 1.0:
            continue

        center = ((pos_u + pos_v) / 2).tolist()
        brace = make_cylinder(member_t / 4, brace_len, center=tuple(center))

        direction = pos_v - pos_u
        direction_norm = direction / np.linalg.norm(direction)
        z_axis = np.array([0, 0, 1])
        if not np.allclose(direction_norm, z_axis, atol=1e-6):
            axis = np.cross(z_axis, direction_norm)
            axis_len = np.linalg.norm(axis)
            if axis_len > 1e-8:
                axis = axis / axis_len
                angle = math.acos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                rot = trimesh.transformations.rotation_matrix(angle, axis, point=center)
                brace.apply_transform(rot)

        parts.append(brace)

    return assemble_meshes(parts)
