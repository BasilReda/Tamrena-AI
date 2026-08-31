import math
from dataclasses import dataclass


@dataclass
class ComputedAngle:
    """One computed angle, ready for the renderer to draw.

    This is the single contract between the analysis layer and the rendering
    layer: ``GymEngine`` produces one ``ComputedAngle`` per ``AngleCounterRule`` and
    per ``AngleValidationRule``, and the renderer iterates over them without knowing
    which exercise or rule produced them. Adding a rule (or a whole new
    exercise) therefore needs zero renderer changes.

    In 3D mode: angle is computed from world_landmarks (3D), but vertex is still
    2D pixel (x,y) for drawing on screen.
    """

    name: str
    vertex: tuple          # pixel (x, y) of the middle/vertex joint - always 2D for rendering
    angle: float | None   # None when the angle could not be computed - now can be 3D angle
    is_error: bool         # True -> draw with the error colour
    is_3d: bool = True     # True if this angle was computed in 3D space


def calc_angle(a, b, c):
    """2D angle calculation (legacy, pixel space) - kept for rendering fallback."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag1 = math.hypot(*ba)
    mag2 = math.hypot(*bc)

    if mag1 == 0 or mag2 == 0:
        return None

    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def calc_angle_3d(a, b, c):
    """
    3D angle calculation from world landmarks (x,y,z in meters).
    
    This is camera-independent and measures true body angles.
    Example: elbow angle is same whether filmed from front or side.
    
    Args:
        a, b, c: tuples (x, y, z) - world coordinates in meters
                 b is vertex
    Returns:
        angle in degrees, or None if degenerate
    """
    # Vectors BA and BC in 3D
    ba = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    bc = (c[0] - b[0], c[1] - b[1], c[2] - b[2])

    dot = ba[0] * bc[0] + ba[1] * bc[1] + ba[2] * bc[2]
    
    mag1 = math.sqrt(ba[0]**2 + ba[1]**2 + ba[2]**2)
    mag2 = math.sqrt(bc[0]**2 + bc[1]**2 + bc[2]**2)

    if mag1 == 0 or mag2 == 0:
        return None

    # Clamp for numerical stability
    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def get_points(indices, landmarks, w, h, threshold: float = 0.5):
    """Get 2D pixel points for rendering - ALWAYS 2D."""
    pts = []
    for i in indices:
        lm = landmarks[i]
        if hasattr(lm, "visibility") and lm.visibility < threshold:
            continue
        pts.append((int(lm.x * w), int(lm.y * h)))
    return pts


def get_points_3d(indices, world_landmarks, threshold: float = 0.5):
    """
    Get 3D world points for angle calculation - ALWAYS 3D.
    
    world_landmarks: list of 33 world landmarks (x,y,z in meters)
    Returns: list of (x, y, z) tuples
    """
    pts = []
    for i in indices:
        if i >= len(world_landmarks):
            continue
        lm = world_landmarks[i]
        # World landmarks may have visibility (if using pose_landmarks as fallback in tests)
        # Only skip if visibility exists and is below threshold
        try:
            vis = getattr(lm, 'visibility', None)
            if vis is not None and vis < threshold:
                continue
        except (AttributeError, TypeError):
            pass
        # World coordinates are already in meters, not normalized
        x = getattr(lm, 'x', 0)
        y = getattr(lm, 'y', 0)
        z = getattr(lm, 'z', 0)
        pts.append((x, y, z))
    return pts



def calc_vertical_ratio(points, shoulder_pts, hip_pts):
    """t = (hip_y - point_y) / (hip_y - shoulder_y).

    Works on either 2D pixel points or 3D world points — only uses index
    [1] (y), so it's space-agnostic. Returns None if any input list is
    empty or the hip/shoulder span is degenerate.
    """
    if not points or not shoulder_pts or not hip_pts:
        return None
    point_y = sum(p[1] for p in points) / len(points)
    shoulder_y = sum(p[1] for p in shoulder_pts) / len(shoulder_pts)
    hip_y = sum(p[1] for p in hip_pts) / len(hip_pts)
    span = hip_y - shoulder_y
    if span == 0:
        return None
    return (hip_y - point_y) / span
