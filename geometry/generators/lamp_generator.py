# geometry/generators/lamp_generator.py
"""Generate lamp meshes from genomes."""

from __future__ import annotations

import math

import numpy as np
import trimesh

from core.genome.genome import Genome
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.graph_builder import build_graph
from geometry.primitives.primitives import make_box, make_cylinder, make_frustum
from geometry.composition.assembler import assemble_meshes


def generate_lamp_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a lamp mesh from a genome."""
    g = genome.genes
    G = build_graph(genome, LAMP_GENE_CATALOG)

    parts: list[trimesh.Trimesh] = []

    member_t = g["member_thickness"]
    head_d = g["head_diameter"]
    shade = g.get("shade_type", "cone")
    taper = g["taper_ratio"]

    # Build parts from graph edges
    for u, v, data in G.edges(data=True):
        pos_u = np.array(G.nodes[u]["pos"])
        pos_v = np.array(G.nodes[v]["pos"])
        seg_len = float(np.linalg.norm(pos_u - pos_v))
        if seg_len < 1.0:
            continue

        center = tuple(((pos_u + pos_v) / 2).tolist())
        r = member_t / 2

        if data["edge_type"] == "support_member":
            part = make_frustum(r, r * taper, seg_len, center=center)
        else:
            part = make_cylinder(r * 0.6, seg_len, center=center)

        # Orient along edge direction
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

    # Lamp head/shade
    head_node = G.nodes.get("head")
    if head_node:
        head_pos = head_node["pos"]
        shade_h = head_d * 0.6
        if shade == "cone":
            head_mesh = make_frustum(head_d / 2, head_d / 6, shade_h,
                                     center=(head_pos[0], head_pos[1], head_pos[2] + shade_h / 2))
        elif shade == "dome":
            head_mesh = trimesh.creation.icosphere(radius=head_d / 2)
            head_mesh.apply_translation(head_pos)
        elif shade == "flat":
            head_mesh = make_box(head_d, head_d, shade_h * 0.3,
                                 center=(head_pos[0], head_pos[1], head_pos[2]))
        else:  # cylinder or none
            head_mesh = make_cylinder(head_d / 2, shade_h,
                                      center=(head_pos[0], head_pos[1], head_pos[2] + shade_h / 2))
        parts.append(head_mesh)

    # Base plate
    base_node = G.nodes.get("base")
    if base_node:
        base_pos = base_node["pos"]
        base_r = g["width"] * 0.3
        base_h = member_t * 0.5
        base = make_cylinder(base_r, base_h,
                             center=(base_pos[0], base_pos[1], base_pos[2] + base_h / 2))
        parts.append(base)

    return assemble_meshes(parts)
