"""Tests for physics/heuristics/thickness.py."""

import networkx as nx

from physics.heuristics.thickness import check_thickness, DEFAULT_MIN_THICKNESS_MM
from physics.materials.material_db import get_material


def _wood():
    return get_material("wood")


def test_thick_members_pass():
    G = nx.Graph()
    genes = {"member_thickness": 30.0, "top_thickness": 20.0}
    result = check_thickness(G, genes, _wood())
    assert result.passed is True
    assert result.min_thickness_found == 20.0
    assert result.failure_reasons == []
    assert result.score == 1.0


def test_thin_member_fails():
    G = nx.Graph()
    genes = {"member_thickness": 3.0, "top_thickness": 20.0}
    result = check_thickness(G, genes, _wood())
    assert result.passed is False
    assert "Support member" in result.failure_reasons[0]
    assert result.score < 1.0


def test_material_modifier_affects_threshold():
    G = nx.Graph()
    genes = {"member_thickness": 6.0, "top_thickness": 10.0}
    # Steel has slenderness_modifier=1.5, so effective_min = 8/1.5 = 5.33
    steel = get_material("steel")
    result = check_thickness(G, genes, steel)
    assert result.passed is True

    # Stone_like has modifier=0.6, so effective_min = 8/0.6 = 13.33
    stone = get_material("stone_like")
    result = check_thickness(G, genes, stone)
    assert result.passed is False


def test_stem_diameter_checked_for_lamps():
    G = nx.Graph()
    genes = {"member_thickness": 30.0, "stem_diameter": 3.0}
    result = check_thickness(G, genes, _wood())
    assert result.passed is False
    assert any("Stem" in r for r in result.failure_reasons)


def test_no_genes_produces_pass():
    """If no relevant genes exist, nothing to fail."""
    G = nx.Graph()
    genes = {"member_thickness": 20.0}
    result = check_thickness(G, genes, _wood())
    assert result.passed is True


def test_score_proportional():
    G = nx.Graph()
    # member_thickness = half of required
    wood = _wood()
    effective_min = DEFAULT_MIN_THICKNESS_MM / wood.slenderness_modifier
    genes = {"member_thickness": effective_min / 2, "top_thickness": 50.0}
    result = check_thickness(G, genes, wood)
    assert result.score == pytest.approx(0.5, abs=0.1)


import pytest
