"""Gene catalog for the chair family (lite)."""

from core.genome.gene_types import GeneSpec, GeneType

CHAIR_GENE_CATALOG: list[GeneSpec] = [
    # Layer 1: Family / Archetype
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["chair_family_lite"], default="chair_family_lite"),
    GeneSpec("subtype", GeneType.CATEGORICAL, layer=1,
             categories=["dining", "lounge", "stool", "office"], default="dining"),
    GeneSpec("topology_family", GeneType.CATEGORICAL, layer=1,
             categories=["skeletal", "monolithic", "hybrid"], default="skeletal"),
    GeneSpec("symmetry_mode", GeneType.CATEGORICAL, layer=1,
             categories=["bilateral", "none"], default="bilateral"),
    GeneSpec("support_strategy", GeneType.CATEGORICAL, layer=1,
             categories=["four_leg", "sled", "cantilever", "pedestal"], default="four_leg"),
    GeneSpec("decorative_bias", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.3),
    GeneSpec("monolithic_ratio", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.0),

    # Layer 2: Structural Graph
    GeneSpec("support_count", GeneType.INTEGER, layer=2,
             min_val=1, max_val=6, default=4),
    GeneSpec("branch_depth", GeneType.INTEGER, layer=2,
             min_val=0, max_val=2, default=0),
    GeneSpec("brace_count", GeneType.INTEGER, layer=2,
             min_val=0, max_val=6, default=0),
    GeneSpec("back_present", GeneType.BOOLEAN, layer=2, default=True),
    GeneSpec("arm_present", GeneType.BOOLEAN, layer=2, default=False),
    GeneSpec("connectivity_density", GeneType.CONTINUOUS, layer=2,
             min_val=0.0, max_val=1.0, default=0.3),

    # Layer 3: Continuous Shape
    GeneSpec("width", GeneType.CONTINUOUS, layer=3,
             min_val=300.0, max_val=800.0, default=450.0),
    GeneSpec("depth", GeneType.CONTINUOUS, layer=3,
             min_val=300.0, max_val=700.0, default=450.0),
    GeneSpec("height", GeneType.CONTINUOUS, layer=3,
             min_val=600.0, max_val=1200.0, default=850.0),
    GeneSpec("seat_height", GeneType.CONTINUOUS, layer=3,
             min_val=350.0, max_val=550.0, default=450.0),
    GeneSpec("back_height", GeneType.CONTINUOUS, layer=3,
             min_val=150.0, max_val=700.0, default=400.0),
    GeneSpec("back_angle", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=30.0, default=5.0),
    GeneSpec("member_thickness", GeneType.CONTINUOUS, layer=3,
             min_val=10.0, max_val=80.0, default=30.0),
    GeneSpec("taper_ratio", GeneType.CONTINUOUS, layer=3,
             min_val=0.5, max_val=1.5, default=1.0),
    GeneSpec("curve_bias", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("fillet_radius", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=15.0, default=2.0),

    # Layer 4: Optional Surface
    GeneSpec("perforation_flag", GeneType.BOOLEAN, layer=4, default=False),
    GeneSpec("perforation_density", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("cutout_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("ribbing_intensity", GeneType.CONTINUOUS, layer=4,
             min_val=0.0, max_val=1.0, default=0.0),
    GeneSpec("asymmetry_offset_x", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
    GeneSpec("asymmetry_offset_y", GeneType.CONTINUOUS, layer=4,
             min_val=-0.2, max_val=0.2, default=0.0),
]
