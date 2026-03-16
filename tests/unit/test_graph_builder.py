"""Tests for genome-to-graph builder."""

import random

import networkx as nx

from core.genome.genome import Genome
from core.genome.table_genes import TABLE_GENE_CATALOG
from core.genome.lamp_genes import LAMP_GENE_CATALOG
from core.genome.chair_genes import CHAIR_GENE_CATALOG
from core.genome.graph_builder import build_graph


def test_table_graph_has_surface_node():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    surface_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "surface"]
    assert len(surface_nodes) >= 1


def test_table_graph_has_support_nodes():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    support_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "ground_anchor"]
    assert len(support_nodes) >= 1


def test_table_graph_is_connected():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    assert nx.is_connected(G)


def test_table_graph_edges_have_types():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    for u, v, d in G.edges(data=True):
        assert "edge_type" in d


def test_lamp_graph_has_head_node():
    genome = Genome.random_init(LAMP_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, LAMP_GENE_CATALOG)
    head_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "head"]
    assert len(head_nodes) >= 1


def test_chair_graph_has_seat():
    genome = Genome.random_init(CHAIR_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, CHAIR_GENE_CATALOG)
    seat_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "surface"]
    assert len(seat_nodes) >= 1


def test_graph_deterministic():
    g1 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    g2 = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G1 = build_graph(g1, TABLE_GENE_CATALOG)
    G2 = build_graph(g2, TABLE_GENE_CATALOG)
    assert list(G1.nodes) == list(G2.nodes)
    assert list(G1.edges) == list(G2.edges)


def test_graph_nodes_have_positions():
    genome = Genome.random_init(TABLE_GENE_CATALOG, random.Random(42))
    G = build_graph(genome, TABLE_GENE_CATALOG)
    for n, d in G.nodes(data=True):
        assert "pos" in d, f"Node {n} missing 'pos'"
        assert len(d["pos"]) == 3
