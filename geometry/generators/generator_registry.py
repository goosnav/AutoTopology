# geometry/generators/generator_registry.py
"""Registry dispatching genome to family-specific mesh generator."""

from __future__ import annotations

import trimesh

from core.genome.genome import Genome


def generate_mesh(genome: Genome) -> trimesh.Trimesh:
    """Generate a mesh from a genome, dispatching by family."""
    family = genome.genes.get("family_name")
    if family == "table_family":
        from geometry.generators.table_generator import generate_table_mesh
        return generate_table_mesh(genome)
    elif family == "lamp_family":
        from geometry.generators.lamp_generator import generate_lamp_mesh
        return generate_lamp_mesh(genome)
    elif family == "chair_family_lite":
        from geometry.generators.chair_generator import generate_chair_mesh
        return generate_chair_mesh(genome)
    raise ValueError(f"Unknown family: {family}")
