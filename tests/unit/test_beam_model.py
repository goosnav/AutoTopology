"""Tests for physics/beam/beam_model.py."""

import math

import networkx as nx
import numpy as np

from physics.beam.beam_model import (
    analyze_beams,
    SLENDERNESS_HARD_FAIL,
    SLENDERNESS_WARN,
)
from physics.materials.material_db import get_material


def _make_table_graph(height=750, member_t=30):
    """Simple 4-leg table graph."""
    G = nx.Graph()
    G.add_node("top", node_type="surface", pos=(0, 0, height))
    positions = [(-300, -200), (300, -200), (300, 200), (-300, 200)]
    for i, (x, y) in enumerate(positions):
        anchor = f"anchor_{i}"
        leg = f"leg_{i}"
        G.add_node(anchor, node_type="surface_anchor", pos=(x, y, height))
        G.add_node(leg, node_type="ground_anchor", pos=(x, y, 0))
        G.add_edge("top", anchor, edge_type="panel_attachment")
        G.add_edge(anchor, leg, edge_type="support_member")
    return G


def test_normal_table_passes():
    G = _make_table_graph()
    genes = {"member_thickness": 30.0, "taper_ratio": 0.8}
    result = analyze_beams(G, genes, get_material("wood"))
    assert result.passed is True
    assert len(result.members) == 4  # 4 support members
    assert result.max_slenderness > 0
    assert result.score > 0


def test_very_thin_legs_fail():
    G = _make_table_graph(height=1000)
    genes = {"member_thickness": 5.0, "taper_ratio": 1.0}
    result = analyze_beams(G, genes, get_material("wood"))
    # 1000mm / 5mm = 200 slenderness >> hard fail
    assert result.max_slenderness > SLENDERNESS_HARD_FAIL
    assert result.passed is False
    assert result.slenderness_score == 0.0


def test_slenderness_score_gradient():
    G = _make_table_graph(height=500)
    wood = get_material("wood")

    # Thick legs: low slenderness
    genes_thick = {"member_thickness": 50.0, "taper_ratio": 1.0}
    result_thick = analyze_beams(G, genes_thick, wood)

    # Thin legs: higher slenderness
    genes_thin = {"member_thickness": 20.0, "taper_ratio": 1.0}
    result_thin = analyze_beams(G, genes_thin, wood)

    assert result_thick.slenderness_score >= result_thin.slenderness_score


def test_braces_included_in_analysis():
    G = _make_table_graph()
    # Add a brace
    G.add_node("brace_0", node_type="brace_point", pos=(0, -200, 250))
    G.add_edge("leg_0", "brace_0", edge_type="brace_member")
    G.add_edge("leg_1", "brace_0", edge_type="brace_member")

    genes = {"member_thickness": 30.0, "taper_ratio": 1.0}
    result = analyze_beams(G, genes, get_material("wood"))
    # Should have 4 support + 2 brace members
    assert len(result.members) == 6


def test_steel_more_forgiving_than_stone():
    G = _make_table_graph()
    genes = {"member_thickness": 25.0, "taper_ratio": 1.0}

    steel_result = analyze_beams(G, genes, get_material("steel"))
    stone_result = analyze_beams(G, genes, get_material("stone_like"))

    # Steel has higher slenderness_modifier (1.5 vs 0.6)
    # so effective diameter is larger -> lower slenderness ratio
    assert steel_result.max_slenderness < stone_result.max_slenderness


def test_member_analysis_has_correct_fields():
    G = _make_table_graph()
    genes = {"member_thickness": 30.0, "taper_ratio": 1.0}
    result = analyze_beams(G, genes, get_material("wood"))
    member = result.members[0]
    assert member.length > 0
    assert member.thickness > 0
    assert member.slenderness_ratio > 0
    assert member.estimated_deflection_mm >= 0
    assert member.span_deflection_ratio > 0
