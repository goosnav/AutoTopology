"""Mesh-to-image renderer.

Renders a trimesh mesh from a given camera transform to a PIL Image.
Uses pyrender with offscreen rendering if available, falls back to
trimesh's built-in scene rendering.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import trimesh
from PIL import Image

from vision.collage.camera import DEFAULT_FOV_DEG


# Default render resolution per view
DEFAULT_RESOLUTION = (512, 512)
# Neutral background color (RGB)
BACKGROUND_COLOR = (220, 220, 220, 255)


def render_view(
    mesh: trimesh.Trimesh,
    camera_transform: np.ndarray,
    resolution: tuple[int, int] = DEFAULT_RESOLUTION,
    fov_deg: float = DEFAULT_FOV_DEG,
) -> Image.Image:
    """Render a mesh from a given camera viewpoint.

    Attempts pyrender offscreen first, falls back to trimesh scene rendering,
    then to a simple wireframe projection if all else fails.

    Args:
        mesh: The mesh to render.
        camera_transform: 4x4 camera-to-world transform.
        resolution: (width, height) in pixels.
        fov_deg: Camera field of view.

    Returns:
        PIL Image of the rendered view.
    """
    # Try pyrender offscreen first
    image = _try_pyrender(mesh, camera_transform, resolution, fov_deg)
    if image is not None:
        return image

    # Try trimesh scene rendering
    image = _try_trimesh_scene(mesh, camera_transform, resolution, fov_deg)
    if image is not None:
        return image

    # Fallback: simple orthographic wireframe projection
    return _render_wireframe(mesh, camera_transform, resolution)


def _try_pyrender(
    mesh: trimesh.Trimesh,
    camera_transform: np.ndarray,
    resolution: tuple[int, int],
    fov_deg: float,
) -> Optional[Image.Image]:
    """Try rendering with pyrender offscreen."""
    try:
        import pyrender
        import os
        os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

        scene = pyrender.Scene(
            bg_color=[c / 255 for c in BACKGROUND_COLOR],
            ambient_light=[0.3, 0.3, 0.3],
        )

        py_mesh = pyrender.Mesh.from_trimesh(mesh)
        scene.add(py_mesh)

        camera = pyrender.PerspectiveCamera(yfov=np.radians(fov_deg))
        scene.add(camera, pose=camera_transform)

        light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
        scene.add(light, pose=camera_transform)

        renderer = pyrender.OffscreenRenderer(*resolution)
        color, _ = renderer.render(scene)
        renderer.delete()

        return Image.fromarray(color)
    except Exception:
        return None


def _try_trimesh_scene(
    mesh: trimesh.Trimesh,
    camera_transform: np.ndarray,
    resolution: tuple[int, int],
    fov_deg: float,
) -> Optional[Image.Image]:
    """Try rendering with trimesh's built-in scene."""
    try:
        scene = trimesh.Scene(mesh)
        scene.camera.resolution = resolution
        scene.camera.fov = (fov_deg, fov_deg * resolution[1] / resolution[0])
        scene.camera_transform = camera_transform

        data = scene.save_image(resolution=resolution, visible=False)
        if data and len(data) > 0:
            from io import BytesIO
            return Image.open(BytesIO(data)).convert("RGBA")
    except Exception:
        pass
    return None


def _render_wireframe(
    mesh: trimesh.Trimesh,
    camera_transform: np.ndarray,
    resolution: tuple[int, int],
) -> Image.Image:
    """Fallback: project mesh edges onto a 2D image.

    Always works — no GPU or display required.
    """
    w, h = resolution
    img = Image.new("RGBA", (w, h), BACKGROUND_COLOR)

    if len(mesh.vertices) == 0:
        return img

    # Transform vertices to camera space
    cam_inv = np.linalg.inv(camera_transform)
    verts_world = np.hstack([mesh.vertices, np.ones((len(mesh.vertices), 1))])
    verts_cam = (cam_inv @ verts_world.T).T[:, :3]

    # Simple orthographic projection
    if len(verts_cam) == 0:
        return img

    # Normalize to image coordinates
    xy = verts_cam[:, :2]
    z = verts_cam[:, 2]

    # Filter vertices in front of camera (negative Z in OpenGL convention)
    mask = z < 0
    if not mask.any():
        return img

    xy_visible = xy[mask]
    x_min, x_max = xy_visible[:, 0].min(), xy_visible[:, 0].max()
    y_min, y_max = xy_visible[:, 1].min(), xy_visible[:, 1].max()

    x_range = max(x_max - x_min, 1)
    y_range = max(y_max - y_min, 1)
    scale = min((w - 40) / x_range, (h - 40) / y_range)

    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2

    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)

    # Draw edges from mesh face boundaries
    edges_drawn = set()
    for face in mesh.faces:
        for i in range(3):
            a, b = int(face[i]), int(face[(i + 1) % 3])
            edge_key = (min(a, b), max(a, b))
            if edge_key in edges_drawn:
                continue
            edges_drawn.add(edge_key)

            if not (mask[a] and mask[b]):
                continue

            x1 = int((xy[a, 0] - x_center) * scale + w / 2)
            y1 = int(-(xy[a, 1] - y_center) * scale + h / 2)
            x2 = int((xy[b, 0] - x_center) * scale + w / 2)
            y2 = int(-(xy[b, 1] - y_center) * scale + h / 2)

            draw.line([(x1, y1), (x2, y2)], fill=(80, 80, 80, 255), width=1)

    return img
