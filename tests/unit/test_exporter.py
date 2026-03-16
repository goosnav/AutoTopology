# tests/unit/test_exporter.py
"""Tests for STL exporter."""

import random

from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from geometry.generators.table_generator import generate_table_mesh
from geometry.export.exporter import export_stl


def test_export_creates_file(tmp_path):
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    out = tmp_path / "test.stl"
    export_stl(mesh, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_export_binary_stl(tmp_path):
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    out = tmp_path / "test.stl"
    export_stl(mesh, out)
    data = out.read_bytes()
    assert len(data) > 84


def test_export_with_metadata(tmp_path):
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    mesh = generate_table_mesh(genome)
    out_stl = tmp_path / "test.stl"
    out_json = tmp_path / "test.json"
    export_stl(mesh, out_stl, metadata={"genome_id": genome.genome_id}, metadata_path=out_json)
    assert out_stl.exists()
    assert out_json.exists()

    import json
    meta = json.loads(out_json.read_text())
    assert meta["genome_id"] == genome.genome_id
