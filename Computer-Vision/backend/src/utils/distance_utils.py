"""Distance calculation utilities — 2D and 3D.

This module centralises ALL distance-related helpers so that both
validation.py and any exercise config can import from one place.

All helpers are pure functions (no state, no I/O) and camera-agnostic:
  - 2D functions work on pixel coordinates (rendering / legacy fallback)
  - 3D functions work on world-space metre coordinates (MediaPipe world_landmarks)

Usage:
    from ..utils.distance_utils import (
        calc_distance,
        calc_distance_3d,
        calc_distance_ratio,
        calc_distance_ratio_3d,
        get_landmark_distance,
        get_landmark_distance_3d,
    )
"""

import math
from typing import List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Raw distance helpers (operate on bare (x,y) or (x,y,z) tuples)
# ─────────────────────────────────────────────────────────────────────────────

def calc_distance(p1: Tuple, p2: Tuple) -> float:
    """2D Euclidean distance between two (x, y) pixel points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def calc_distance_3d(p1: Tuple, p2: Tuple) -> float:
    """3D Euclidean distance between two (x, y, z) world-space points (metres)."""
    return math.sqrt(
        (p2[0] - p1[0]) ** 2 +
        (p2[1] - p1[1]) ** 2 +
        (p2[2] - p1[2]) ** 2
    )


def calc_distance_ratio(
    measurement_pts: List[Tuple],
    reference_pts: List[Tuple],
) -> Optional[float]:
    """2D distance ratio: dist(measurement) / dist(reference).

    Returns None when reference distance is zero or fewer than 2 points are
    provided for either set.  The ratio is camera-distance-independent when
    both pairs are measured from the same image.
    """
    if len(measurement_pts) < 2 or len(reference_pts) < 2:
        return None
    dist = calc_distance(measurement_pts[0], measurement_pts[1])
    ref  = calc_distance(reference_pts[0],  reference_pts[1])
    return (dist / ref) if ref != 0 else None


def calc_distance_ratio_3d(
    measurement_pts: List[Tuple],
    reference_pts: List[Tuple],
) -> Optional[float]:
    """3D distance ratio: dist(measurement) / dist(reference) in world space.

    More accurate than the 2D version because depth is included.  Body-size
    and camera-distance independent when the reference is a fixed body segment
    (e.g. shoulder-to-shoulder width).
    """
    if len(measurement_pts) < 2 or len(reference_pts) < 2:
        return None
    dist = calc_distance_3d(measurement_pts[0], measurement_pts[1])
    ref  = calc_distance_3d(reference_pts[0],  reference_pts[1])
    return (dist / ref) if ref != 0 else None


# ─────────────────────────────────────────────────────────────────────────────
# Landmark-aware helpers (extract points from MediaPipe landmark objects)
# ─────────────────────────────────────────────────────────────────────────────

def get_landmark_distance(
    idx_a: int,
    idx_b: int,
    landmarks,
    width: int,
    height: int,
    visibility_threshold: float = 0.5,
) -> Optional[float]:
    """2D pixel distance between two landmarks, with visibility guard.

    Returns None when either landmark is below *visibility_threshold* or is
    out of bounds.
    """
    if landmarks is None or max(idx_a, idx_b) >= len(landmarks):
        return None
    lm_a = landmarks[idx_a]
    lm_b = landmarks[idx_b]
    if (getattr(lm_a, "visibility", 1.0) < visibility_threshold or
            getattr(lm_b, "visibility", 1.0) < visibility_threshold):
        return None
    p1 = (int(lm_a.x * width), int(lm_a.y * height))
    p2 = (int(lm_b.x * width), int(lm_b.y * height))
    return calc_distance(p1, p2)


def get_landmark_distance_3d(
    idx_a: int,
    idx_b: int,
    world_landmarks,
    visibility_threshold: float = 0.5,
) -> Optional[float]:
    """3D world-space distance between two landmarks, with visibility guard.

    Uses world_landmarks (x,y,z in metres from MediaPipe).  Returns None when
    landmarks are unavailable or below *visibility_threshold*.
    """
    if world_landmarks is None or max(idx_a, idx_b) >= len(world_landmarks):
        return None
    lm_a = world_landmarks[idx_a]
    lm_b = world_landmarks[idx_b]
    vis_a = getattr(lm_a, "visibility", None)
    vis_b = getattr(lm_b, "visibility", None)
    if (vis_a is not None and vis_a < visibility_threshold) or \
       (vis_b is not None and vis_b < visibility_threshold):
        return None
    p1 = (getattr(lm_a, "x", 0), getattr(lm_a, "y", 0), getattr(lm_a, "z", 0))
    p2 = (getattr(lm_b, "x", 0), getattr(lm_b, "y", 0), getattr(lm_b, "z", 0))
    return calc_distance_3d(p1, p2)


# ─────────────────────────────────────────────────────────────────────────────
# Normalised body-proportion helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_shoulder_width_3d(world_landmarks, visibility_threshold: float = 0.5) -> Optional[float]:
    """Return 3D shoulder-width (metres) as a normalisation reference.

    Uses landmarks 11 (left shoulder) and 12 (right shoulder).
    Returns None when either shoulder is not visible.
    """
    return get_landmark_distance_3d(11, 12, world_landmarks, visibility_threshold)


def get_shoulder_width_2d(
    landmarks,
    width: int,
    height: int,
    visibility_threshold: float = 0.5,
) -> Optional[float]:
    """Return 2D pixel shoulder-width as a normalisation reference."""
    return get_landmark_distance(11, 12, landmarks, width, height, visibility_threshold)


def get_torso_height_3d(world_landmarks, visibility_threshold: float = 0.5) -> Optional[float]:
    """Return 3D torso height (shoulder-midpoint to hip-midpoint, in metres).

    Used to normalise shoulder-height deltas (e.g. shrug detection) so the
    rule threshold is the same for tall and short athletes.
    Returns None when any required landmark is not visible.
    """
    if world_landmarks is None or len(world_landmarks) <= 24:
        return None
    landmarks_needed = [11, 12, 23, 24]
    lms = []
    for idx in landmarks_needed:
        lm = world_landmarks[idx]
        vis = getattr(lm, "visibility", None)
        if vis is not None and vis < visibility_threshold:
            return None
        lms.append(lm)
    left_shoulder, right_shoulder, left_hip, right_hip = lms
    shoulder_y = (getattr(left_shoulder, "y", 0) + getattr(right_shoulder, "y", 0)) / 2
    hip_y      = (getattr(left_hip,      "y", 0) + getattr(right_hip,      "y", 0)) / 2
    height_val = abs(shoulder_y - hip_y)
    return height_val if height_val > 0 else None
