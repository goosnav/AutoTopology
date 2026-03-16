"""2x2 collage assembly — combines 4 view renders into one image.

Produces a single composite image for VLM scoring input.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import trimesh
from PIL import Image, ImageDraw, ImageFont

from vision.collage.camera import get_four_view_transforms, DEFAULT_FOV_DEG
from vision.collage.renderer import render_view, DEFAULT_RESOLUTION


# Padding between views in pixels
DEFAULT_PADDING = 4
# Label color
LABEL_COLOR = (100, 100, 100, 255)


def render_collage(
    mesh: trimesh.Trimesh,
    resolution_per_view: tuple[int, int] = DEFAULT_RESOLUTION,
    elevation_deg: float = 30.0,
    fov_deg: float = DEFAULT_FOV_DEG,
    padding: int = DEFAULT_PADDING,
    draw_labels: bool = True,
) -> Image.Image:
    """Render a 2x2 collage of 4 isometric views of a mesh.

    Args:
        mesh: The mesh to render.
        resolution_per_view: (width, height) per individual view.
        elevation_deg: Camera elevation angle.
        fov_deg: Camera field of view.
        padding: Pixels between views.
        draw_labels: Whether to draw view labels on each quadrant.

    Returns:
        PIL Image with 4 views in a 2x2 grid.
    """
    views = get_four_view_transforms(mesh, elevation_deg, fov_deg)
    vw, vh = resolution_per_view

    images: list[tuple[str, Image.Image]] = []
    for label, transform in views:
        img = render_view(mesh, transform, resolution_per_view, fov_deg)
        images.append((label, img))

    # Assemble 2x2 grid
    total_w = vw * 2 + padding
    total_h = vh * 2 + padding
    collage = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))

    positions = [
        (0, 0),                    # Top-left: front
        (vw + padding, 0),         # Top-right: right
        (0, vh + padding),         # Bottom-left: back
        (vw + padding, vh + padding),  # Bottom-right: left
    ]

    for (label, img), (x, y) in zip(images, positions):
        # Ensure correct size
        if img.size != resolution_per_view:
            img = img.resize(resolution_per_view, Image.LANCZOS)
        collage.paste(img, (x, y))

        if draw_labels:
            draw = ImageDraw.Draw(collage)
            draw.text(
                (x + 8, y + 4),
                label,
                fill=LABEL_COLOR,
            )

    return collage


def render_and_save_collage(
    mesh: trimesh.Trimesh,
    output_path: Path | str,
    resolution_per_view: tuple[int, int] = DEFAULT_RESOLUTION,
    **kwargs,
) -> Path:
    """Render a collage and save to disk as PNG.

    Args:
        mesh: The mesh to render.
        output_path: Where to save the PNG.
        resolution_per_view: Resolution per view quadrant.
        **kwargs: Additional args passed to render_collage.

    Returns:
        Path to the saved PNG file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    collage = render_collage(mesh, resolution_per_view, **kwargs)
    collage.save(str(output_path), format="PNG")

    return output_path
