"""Geometry quality tests -- verify the mesh pipeline produces real furniture shapes.

These tests go beyond "has vertices + positive volume" and check that the
generated geometry actually matches the gene dimensions, sits on the ground
plane, and has no degenerate faces.
"""

from __future__ import annotations

import io
import random

import numpy as np
import pytest
import trimesh

from core.genome.catalog_registry import get_catalog
from core.genome.genome import Genome
from geometry.generators.generator_registry import generate_mesh
from geometry.mesh_validation.validator import validate_mesh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAMILIES = ["table_family", "lamp_family", "chair_family_lite"]


def _make_genome(family: str, seed: int) -> Genome:
    """Create a random genome for the given family."""
    rng = random.Random(seed)
    catalog = get_catalog(family)
    return Genome.random_init(catalog, rng)


def _make_mesh(family: str, seed: int) -> tuple[Genome, trimesh.Trimesh]:
    """Create a genome and its corresponding mesh."""
    genome = _make_genome(family, seed)
    mesh = generate_mesh(genome)
    return genome, mesh


# ---------------------------------------------------------------------------
# 1. Table top is at the top
# ---------------------------------------------------------------------------


class TestTableTopAtTop:
    """The table top surface should be at z = genome height."""

    @pytest.mark.parametrize("seed", range(10))
    def test_table_z_max_matches_gene_height(self, seed: int) -> None:
        genome, mesh = _make_mesh("table_family", seed)
        gene_h = genome.genes["height"]
        z_max = float(mesh.bounds[1][2])

        # The table top box goes from h - top_t to h, so z_max should
        # match gene height exactly (within floating-point tolerance).
        assert abs(z_max - gene_h) < 1.0, (
            f"Table z_max ({z_max:.1f}) should match gene height ({gene_h:.1f})"
        )


# ---------------------------------------------------------------------------
# 2. Table legs touch the ground
# ---------------------------------------------------------------------------


class TestTableLegsOnGround:
    """The lowest vertices should be near z=0."""

    @pytest.mark.parametrize("seed", range(10))
    def test_table_z_min_near_zero(self, seed: int) -> None:
        genome, mesh = _make_mesh("table_family", seed)
        z_min = float(mesh.bounds[0][2])
        member_t = genome.genes["member_thickness"]

        # Frustum legs can extend slightly below z=0 because the frustum
        # is centered on the midpoint of tilted support members, and the
        # radius at the bottom creates a small overshoot.  The overshoot
        # is bounded by roughly member_thickness / 2.
        tolerance = member_t / 2 + 1.0
        assert z_min >= -tolerance, (
            f"Table z_min ({z_min:.2f}) is too far below ground "
            f"(tolerance -{tolerance:.1f})"
        )
        assert z_min <= 1.0, (
            f"Table z_min ({z_min:.2f}) is floating above ground"
        )


# ---------------------------------------------------------------------------
# 3. Table bounding box roughly matches gene dimensions
# ---------------------------------------------------------------------------


class TestTableBoundingBox:
    """Bounding box width/depth should be within 2x of gene values."""

    @pytest.mark.parametrize("seed", range(10))
    def test_table_width_in_range(self, seed: int) -> None:
        genome, mesh = _make_mesh("table_family", seed)
        gene_w = genome.genes["width"]
        bb_w = float(mesh.bounding_box.extents[0])

        # The bounding box width can exceed gene width slightly because
        # cylindrical legs add their radius beyond the footprint.
        # It should never be more than 2x the gene value.
        assert bb_w <= gene_w * 2.0, (
            f"BB width ({bb_w:.0f}) > 2x gene width ({gene_w:.0f})"
        )
        # It also should not be dramatically smaller (e.g. less than half)
        # unless pedestal with 1 leg.  Allow 0.5x as floor.
        assert bb_w >= gene_w * 0.5, (
            f"BB width ({bb_w:.0f}) < 0.5x gene width ({gene_w:.0f})"
        )

    @pytest.mark.parametrize("seed", range(10))
    def test_table_depth_in_range(self, seed: int) -> None:
        genome, mesh = _make_mesh("table_family", seed)
        gene_d = genome.genes["depth"]
        bb_d = float(mesh.bounding_box.extents[1])

        assert bb_d <= gene_d * 2.0, (
            f"BB depth ({bb_d:.0f}) > 2x gene depth ({gene_d:.0f})"
        )
        assert bb_d >= gene_d * 0.5, (
            f"BB depth ({bb_d:.0f}) < 0.5x gene depth ({gene_d:.0f})"
        )


# ---------------------------------------------------------------------------
# 4. Chair seat is at seat_height
# ---------------------------------------------------------------------------


class TestChairSeatHeight:
    """The mesh should have geometry near the seat_height z-level."""

    @pytest.mark.parametrize("seed", range(10))
    def test_chair_has_vertices_near_seat_height(self, seed: int) -> None:
        genome, mesh = _make_mesh("chair_family_lite", seed)
        seat_h = genome.genes["seat_height"]
        member_t = genome.genes["member_thickness"]
        seat_thickness = max(member_t * 0.5, 15.0)

        z_vals = mesh.vertices[:, 2]

        # The seat box is centered at seat_h - seat_thickness/2, so its
        # top face is at seat_h and bottom face at seat_h - seat_thickness.
        # Vertices should cluster around these z-levels.
        tolerance = seat_thickness + 5.0
        near_seat = np.abs(z_vals - seat_h) < tolerance
        assert near_seat.sum() > 0, (
            f"No vertices within {tolerance:.0f}mm of seat_height "
            f"({seat_h:.0f}mm)"
        )


# ---------------------------------------------------------------------------
# 5. Lamp is taller than it is wide
# ---------------------------------------------------------------------------


class TestLampProportions:
    """A lamp with reasonable gene proportions should be taller than wide.

    NOTE: ~4-5% of random genomes produce squat lamps because the gene
    ranges allow head_diameter (up to 500mm) to exceed overall height
    (as low as 150mm).  This is a real gene-range issue, not a generator
    bug.  We test with a controlled genome where height >> head_diameter.
    """

    def test_lamp_taller_than_wide_controlled(self) -> None:
        """With a genome where height comfortably exceeds head_diameter,
        the mesh bounding box height must exceed its width."""
        rng = random.Random(42)
        catalog = get_catalog("lamp_family")
        genome = Genome.random_init(catalog, rng)
        # Force proportions that should always produce a tall lamp
        genome.genes["height"] = 800.0
        genome.genes["stem_height"] = 600.0
        genome.genes["head_diameter"] = 150.0
        genome.genes["width"] = 200.0

        mesh = generate_mesh(genome)
        bb = mesh.bounding_box.extents
        mesh_height = bb[2]
        mesh_width = max(bb[0], bb[1])

        assert mesh_height > mesh_width, (
            f"Lamp should be taller ({mesh_height:.0f}) than wide "
            f"({mesh_width:.0f})"
        )

    @pytest.mark.parametrize("seed", range(20))
    def test_lamp_taller_than_wide_when_genes_allow(self, seed: int) -> None:
        """Lamps where gene height > 2 * head_diameter should be tall."""
        genome, mesh = _make_mesh("lamp_family", seed)
        gene_h = genome.genes["height"]
        head_d = genome.genes["head_diameter"]

        if gene_h < 2.0 * head_d:
            pytest.skip(
                f"Gene height ({gene_h:.0f}) < 2x head_diameter "
                f"({head_d:.0f}); squat lamp expected"
            )

        bb = mesh.bounding_box.extents
        mesh_height = bb[2]
        mesh_width = max(bb[0], bb[1])

        assert mesh_height > mesh_width, (
            f"Lamp should be taller ({mesh_height:.0f}) than wide "
            f"({mesh_width:.0f}) when gene height >> head diameter"
        )


# ---------------------------------------------------------------------------
# 6. No degenerate faces
# ---------------------------------------------------------------------------


class TestNoDegenerateFaces:
    """No triangle should have zero area."""

    @pytest.mark.parametrize("family", FAMILIES)
    @pytest.mark.parametrize("seed", range(10))
    def test_no_zero_area_faces(self, family: str, seed: int) -> None:
        _, mesh = _make_mesh(family, seed)
        areas = mesh.area_faces
        degenerate = (areas < 1e-10).sum()
        assert degenerate == 0, (
            f"{family} seed={seed}: {degenerate} degenerate (zero-area) "
            f"faces out of {len(areas)}"
        )


# ---------------------------------------------------------------------------
# 7. Mesh centroid near origin XY
# ---------------------------------------------------------------------------


class TestCentroidNearOriginXY:
    """Furniture meshes should be roughly centered around (0, 0) in XY.

    Tables and lamps are symmetric and should have centroid very near
    origin.  Chairs may have Y-offset due to the back panel.
    """

    @pytest.mark.parametrize("seed", range(10))
    def test_table_centroid_xy(self, seed: int) -> None:
        genome, mesh = _make_mesh("table_family", seed)
        cx, cy = float(mesh.centroid[0]), float(mesh.centroid[1])
        bb = mesh.bounding_box.extents

        # Table centroid X and Y should be within 10% of bounding-box
        # half-extents from origin.
        assert abs(cx) < bb[0] * 0.1, (
            f"Table centroid X ({cx:.1f}) too far from origin "
            f"(bb width {bb[0]:.0f})"
        )
        assert abs(cy) < bb[1] * 0.1, (
            f"Table centroid Y ({cy:.1f}) too far from origin "
            f"(bb depth {bb[1]:.0f})"
        )

    @pytest.mark.parametrize("seed", range(10))
    def test_lamp_centroid_xy(self, seed: int) -> None:
        genome, mesh = _make_mesh("lamp_family", seed)
        cx, cy = float(mesh.centroid[0]), float(mesh.centroid[1])
        bb = mesh.bounding_box.extents

        assert abs(cx) < bb[0] * 0.1, (
            f"Lamp centroid X ({cx:.1f}) too far from origin"
        )
        assert abs(cy) < bb[1] * 0.1, (
            f"Lamp centroid Y ({cy:.1f}) too far from origin"
        )

    @pytest.mark.parametrize("seed", range(10))
    def test_chair_centroid_x_near_zero(self, seed: int) -> None:
        """Chair X should be near zero (bilateral symmetry in X)."""
        genome, mesh = _make_mesh("chair_family_lite", seed)
        cx = float(mesh.centroid[0])
        bb = mesh.bounding_box.extents

        # X should be well centered; allow 10% of bounding-box width
        assert abs(cx) < bb[0] * 0.1, (
            f"Chair centroid X ({cx:.1f}) too far from origin"
        )

    @pytest.mark.parametrize("seed", range(10))
    def test_chair_centroid_y_within_bounds(self, seed: int) -> None:
        """Chair Y centroid may be offset by the back panel, but should
        still be inside the bounding box."""
        genome, mesh = _make_mesh("chair_family_lite", seed)
        cy = float(mesh.centroid[1])
        bb_half_y = float(mesh.bounding_box.extents[1]) / 2

        # The centroid should at least be within the bounding box
        assert abs(cy) <= bb_half_y, (
            f"Chair centroid Y ({cy:.1f}) outside bounding box "
            f"(half-extent {bb_half_y:.0f})"
        )


# ---------------------------------------------------------------------------
# 8. Multiple seeds all produce valid meshes
# ---------------------------------------------------------------------------


class TestMultipleSeedsValid:
    """20 seeds per family should all produce meshes with positive volume."""

    @pytest.mark.parametrize("family", FAMILIES)
    def test_20_seeds_positive_volume(self, family: str) -> None:
        failures: list[str] = []
        for seed in range(20):
            genome, mesh = _make_mesh(family, seed)
            report = validate_mesh(mesh)
            if not report.is_acceptable:
                failures.append(
                    f"seed={seed}: {report}"
                )

        assert not failures, (
            f"{family}: {len(failures)}/20 seeds failed validation:\n"
            + "\n".join(failures)
        )


# ---------------------------------------------------------------------------
# 9. STL roundtrip
# ---------------------------------------------------------------------------


class TestSTLRoundtrip:
    """Export to binary STL and reimport; face count should be preserved.

    Vertex counts may differ because STL can merge or split shared
    vertices, but the number of triangular faces must be identical.
    """

    @pytest.mark.parametrize("family", FAMILIES)
    @pytest.mark.parametrize("seed", [0, 7, 42])
    def test_stl_roundtrip_face_count(self, family: str, seed: int) -> None:
        _, mesh = _make_mesh(family, seed)
        original_face_count = len(mesh.faces)

        stl_bytes = mesh.export(file_type="stl")
        reimported = trimesh.load(io.BytesIO(stl_bytes), file_type="stl")

        assert len(reimported.faces) == original_face_count, (
            f"Face count mismatch after STL roundtrip: "
            f"original={original_face_count}, "
            f"reimported={len(reimported.faces)}"
        )

    @pytest.mark.parametrize("family", FAMILIES)
    def test_stl_roundtrip_preserves_volume(self, family: str) -> None:
        """Volume should be preserved within 1% after STL roundtrip."""
        _, mesh = _make_mesh(family, 42)
        original_volume = float(mesh.volume)

        stl_bytes = mesh.export(file_type="stl")
        reimported = trimesh.load(io.BytesIO(stl_bytes), file_type="stl")
        reimported_volume = float(reimported.volume)

        relative_error = abs(reimported_volume - original_volume) / max(original_volume, 1e-6)
        assert relative_error < 0.01, (
            f"Volume changed by {relative_error*100:.2f}% after STL roundtrip "
            f"(original={original_volume:.1f}, reimported={reimported_volume:.1f})"
        )
