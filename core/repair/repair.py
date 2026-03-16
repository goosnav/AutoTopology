"""Genome repair — clamp out-of-range values and fix invalid categoricals.

Spec §24.6: Repair is allowed but bounded.  It must not become a hidden
second generator.  Only valid values from the catalog are substituted.
"""

from __future__ import annotations

import uuid
from typing import List

from core.genome.gene_types import GeneSpec, GeneType
from core.genome.genome import Genome


def repair_genome(genome: Genome, catalog: List[GeneSpec]) -> Genome:
    """Return a new genome with out-of-range / invalid genes corrected.

    - CONTINUOUS / INTEGER: clamp to [min_val, max_val]
    - CATEGORICAL: if value not in categories, replace with the default or first category
    - BOOLEAN: no-op (any bool is valid)
    - Missing genes: filled with spec default

    The input genome is never mutated; a new Genome object is returned.

    Args:
        genome: The genome to repair.
        catalog: Gene specifications.

    Returns:
        New Genome with a new genome_id.
    """
    repaired = dict(genome.genes)
    catalog_map = {s.name: s for s in catalog}

    # Repair existing genes
    for name, value in list(repaired.items()):
        spec = catalog_map.get(name)
        if spec is None:
            continue  # Unknown gene — leave as-is (not our job to strip extras)

        if spec.gene_type == GeneType.CONTINUOUS:
            clamped = max(float(spec.min_val), min(float(spec.max_val), float(value)))
            repaired[name] = clamped

        elif spec.gene_type == GeneType.INTEGER:
            clamped = max(int(spec.min_val), min(int(spec.max_val), int(value)))
            repaired[name] = clamped

        elif spec.gene_type == GeneType.CATEGORICAL:
            if value not in spec.categories:
                # Use default if it's a valid category, else first category
                if spec.default in spec.categories:
                    repaired[name] = spec.default
                else:
                    repaired[name] = spec.categories[0]

        elif spec.gene_type == GeneType.BOOLEAN:
            repaired[name] = bool(value)

    # Fill any missing genes with defaults
    for spec in catalog:
        if spec.name not in repaired:
            repaired[spec.name] = spec.default

    return Genome(genes=repaired, genome_id=uuid.uuid4().hex[:12])
