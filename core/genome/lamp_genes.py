"""Gene catalog for the lamp family."""

from core.genome.gene_types import GeneSpec, GeneType

LAMP_GENE_CATALOG: list[GeneSpec] = [
    # Layer 1: Family / Archetype
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["lamp_family"], default="lamp_family"),
    GeneSpec("subtype", GeneType.CATEGORICAL, layer=1,
             categories=["desk", "floor", "pendant", "wall"], default="desk"),
    GeneSpec("topology_family", GeneType.CATEGORICAL, layer=1,
             categories=["skeletal", "monolithic", "hybrid"], default="skeletal"),
    GeneSpec("symmetry_mode", GeneType.CATEGORICAL, layer=1,
             categories=["bilateral", "radial", "none"], default="radial"),
    GeneSpec("support_strategy", GeneType.CATEGORICAL, layer=1,
             categories=["base_plate", "tripod", "clamp", "weighted"], default="base_plate"),
    GeneSpec("decorative_bias", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.5),
    GeneSpec("monolithic_ratio", GeneType.CONTINUOUS, layer=1,
             min_val=0.0, max_val=1.0, default=0.0),

    # Layer 2: Structural Graph
    GeneSpec("support_count", GeneType.INTEGER, layer=2,
             min_val=1, max_val=5, default=1),
    GeneSpec("branch_depth", GeneType.INTEGER, layer=2,
             min_val=0, max_val=3, default=0),
    GeneSpec("brace_count", GeneType.INTEGER, layer=2,
             min_val=0, max_val=4, default=0),
    GeneSpec("shade_type", GeneType.CATEGORICAL, layer=2,
             categories=["cone", "dome", "cylinder", "flat", "none"], default="cone"),
    GeneSpec("connectivity_density", GeneType.CONTINUOUS, layer=2,
             min_val=0.0, max_val=1.0, default=0.2),

    # Layer 3: Continuous Shape
    GeneSpec("width", GeneType.CONTINUOUS, layer=3,
             min_val=50.0, max_val=600.0, default=200.0),
    GeneSpec("depth", GeneType.CONTINUOUS, layer=3,
             min_val=50.0, max_val=600.0, default=200.0),
    GeneSpec("height", GeneType.CONTINUOUS, layer=3,
             min_val=150.0, max_val=1800.0, default=450.0),
    GeneSpec("stem_height", GeneType.CONTINUOUS, layer=3,
             min_val=50.0, max_val=1500.0, default=300.0),
    GeneSpec("head_diameter", GeneType.CONTINUOUS, layer=3,
             min_val=30.0, max_val=500.0, default=150.0),
    GeneSpec("member_thickness", GeneType.CONTINUOUS, layer=3,
             min_val=5.0, max_val=60.0, default=15.0),
    GeneSpec("taper_ratio", GeneType.CONTINUOUS, layer=3,
             min_val=0.3, max_val=2.0, default=1.0),
    GeneSpec("curve_bias", GeneType.CONTINUOUS, layer=3,
             min_val=0.0, max_val=1.0, default=0.2),
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
