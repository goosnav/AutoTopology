"""Tests for physics/heuristics/connectivity.py."""

import networkx as nx

from physics.heuristics.connectivity import check_connectivity


def _make_table_graph():
    """Simple table: top -> 4 legs to ground."""
    G = nx.Graph()
    G.add_node("top", node_type="surface", pos=(0, 0, 750))
    for i, (x, y) in enumerate([(-300, -200), (300, -200), (300, 200), (-300, 200)]):
        anchor = f"anchor_{i}"
        leg = f"leg_{i}"
        G.add_node(anchor, node_type="surface_anchor", pos=(x, y, 750))
        G.add_node(leg, node_type="ground_anchor", pos=(x, y, 0))
        G.add_edge("top", anchor, edge_type="panel_attachment")
        G.add_edge(anchor, leg, edge_type="support_member")
    return G


def test_connected_table():
    G = _make_table_graph()
    result = check_connectivity(G)
    assert result.is_connected is True
    assert result.surfaces_grounded == 1
    assert result.surfaces_total == 1
    assert result.score == 1.0
    assert result.failure_reasons == []


def test_disconnected_surface():
    G = _make_table_graph()
    # Add a floating shelf with no path to ground
    G.add_node("shelf", node_type="surface", pos=(0, 0, 400))
    result = check_connectivity(G)
    assert result.is_connected is False
    assert result.surfaces_grounded == 1
    assert result.surfaces_total == 2
    assert result.score == 0.5
    assert len(result.failure_reasons) == 1


def test_no_ground_anchors():
    G = nx.Graph()
    G.add_node("top", node_type="surface", pos=(0, 0, 750))
    G.add_node("leg", node_type="surface_anchor", pos=(0, 0, 0))
    G.add_edge("top", "leg", edge_type="support_member")
    result = check_connectivity(G)
    assert result.is_connected is False
    assert result.score == 0.0


def test_empty_graph():
    G = nx.Graph()
    result = check_connectivity(G)
    assert result.is_connected is False
    assert result.surfaces_total == 0


def test_lamp_head_is_treated_as_surface():
    G = nx.Graph()
    G.add_node("head", node_type="head", pos=(0, 0, 500))
    G.add_node("base", node_type="ground_anchor", pos=(0, 0, 0))
    G.add_edge("head", "base", edge_type="support_member")
    result = check_connectivity(G)
    assert result.is_connected is True
    assert result.surfaces_grounded == 1
