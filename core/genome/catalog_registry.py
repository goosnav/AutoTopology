"""Registry mapping family names to their gene catalogs."""

from core.genome.gene_types import GeneSpec
from core.genome.table_genes import TABLE_GENE_CATALOG
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.chair_genes import CHAIR_GENE_CATALOG

_CATALOGS: dict[str, list[GeneSpec]] = {
    "table_family": TABLE_GENE_CATALOG,
    "lamp_family": LAMP_GENE_CATALOG,
    "chair_family_lite": CHAIR_GENE_CATALOG,
}


def get_catalog(family_name: str) -> list[GeneSpec]:
    """Return the gene catalog for a given family name."""
    if family_name not in _CATALOGS:
        raise ValueError(f"Unknown family: {family_name}. Available: {list(_CATALOGS.keys())}")
    return _CATALOGS[family_name]
