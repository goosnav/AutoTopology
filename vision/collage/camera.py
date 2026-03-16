"""4-view isometric camera setup.

Produces deterministic camera transforms for four views around an object:
front, right, back, left — all at a consistent elevation angle.
"""

from __future__ import annotations

import math

import numpy as np
import trimesh


# Default camera settings
DEFAULT_ELEVATION_DEG = 30.0
DEFAULT_FOV_DEG = 60.0
AZIMUTHS_DEG = (0.0, 90.0, 180.0, 270.0)  # Front, Right, Back, Left
VIEW_LABELS = ("front", "right", "back", "left")


def compute_camera_distance(mesh: trimesh.Trimesh, fov_deg: float = DEFAULT_FOV_DEG) -> float:
    """Compute camera distance to frame the entire mesh in view."""
    extents = mesh.bounding_box.extents
    max_extent = float(max(extents))
    fov_rad = math.radians(fov_deg / 2)
    # Add 20% padding
    distance = (max_extent / 2) / math.tan(fov_rad) * 1.2
    return max(distance, 1.0)


def camera_transform(
    azimuth_deg: float,
    elevation_deg: float,
    distance: float,
    target: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> np.ndarray:
    """Compute a 4x4 camera transform looking at target from given angles.

    Args:
        azimuth_deg: Horizontal angle in degrees (0 = front/+Y).
        elevation_deg: Vertical angle in degrees above horizon.
        distance: Distance from target.
        target: Point the camera looks at.

    Returns:
        4x4 transform matrix (camera-to-world).
    """
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)

    # Camera position in spherical coordinates
    x = distance * math.cos(el) * math.sin(az) + target[0]
    y = distance * math.cos(el) * math.cos(az) + target[1]
    z = distance * math.sin(el) + target[2]

    camera_pos = np.array([x, y, z])
    target_pos = np.array(target)

    # Look-at matrix
    forward = target_pos - camera_pos
    forward = forward / np.linalg.norm(forward)

    world_up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right_norm = np.linalg.norm(right)
    if right_norm < 1e-6:
        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, world_up)
        right_norm = np.linalg.norm(right)
    right = right / right_norm

    up = np.cross(right, forward)
    up = up / np.linalg.norm(up)

    # Build 4x4 camera-to-world transform
    # OpenGL convention: camera looks down -Z
    transform = np.eye(4)
    transform[:3, 0] = right
    transform[:3, 1] = up
    transform[:3, 2] = -forward
    transform[:3, 3] = camera_pos

    return transform


def get_four_view_transforms(
    mesh: trimesh.Trimesh,
    elevation_deg: float = DEFAULT_ELEVATION_DEG,
    fov_deg: float = DEFAULT_FOV_DEG,
) -> list[tuple[str, np.ndarray]]:
    """Compute camera transforms for 4 isometric views.

    Args:
        mesh: The mesh to frame.
        elevation_deg: Camera elevation above horizon.
        fov_deg: Field of view in degrees.

    Returns:
        List of (view_label, 4x4_transform) tuples.
    """
    center = mesh.centroid.tolist()
    distance = compute_camera_distance(mesh, fov_deg)

    views = []
    for label, azimuth in zip(VIEW_LABELS, AZIMUTHS_DEG):
        transform = camera_transform(azimuth, elevation_deg, distance, tuple(center))
        views.append((label, transform))

    return views
