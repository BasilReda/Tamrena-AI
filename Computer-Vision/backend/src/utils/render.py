import functools
import math

import cv2

from .geometry import ComputedAngle


# ── Stats overlay layout ────────────────────────────────────────────────────
STATS_MARGIN = 20
STATS_PADDING = 10
STATS_LINE_HEIGHT = 22         # reduced from 25 for more compact box
STATS_FONT = cv2.FONT_HERSHEY_SIMPLEX
STATS_FONT_SCALE = 0.55        # slightly smaller for more text
STATS_THICKNESS = 2
STATS_BG_ALPHA = 0.5
# Fixed box - compact and stable, wraps instead of truncates
STATS_FIXED_WIDTH = 400        # slightly wider to fit more text per line
STATS_MAX_LINES = 9            # reduced from 11 - 7 core + 2 feedback (wrapped)
STATS_FIXED_HEIGHT = STATS_MAX_LINES * STATS_LINE_HEIGHT + STATS_PADDING * 2
STATS_MAX_FEEDBACK = 2         # reduced from 4 - only show 2 most recent feedback
STATS_MAX_TEXT_WIDTH = STATS_FIXED_WIDTH - STATS_PADDING * 2


def draw_skeleton(frame, pts, colors, is_bad=False, custom_color=None):
    if len(pts) < 3:
        return
    SKEL_COLOR = (255, 255, 255)
    if custom_color is not None:
        line_color = custom_color
        point_color = custom_color
    else:
        line_color = colors.ERROR if is_bad else SKEL_COLOR
        point_color = colors.ERROR if is_bad else SKEL_COLOR
    LINE_W = 5
    RADIUS = 12
    BORDER_W = 8
    def _edge_point(src, dst, r):
        dx, dy = dst[0] - src[0], dst[1] - src[1]
        dist = math.hypot(dx, dy)
        if dist < 1:
            return src
        return (int(src[0] + dx / dist * r), int(src[1] + dy / dist * r))
    p0, p1, p2 = pts[0], pts[1], pts[2]
    cv2.line(frame, _edge_point(p0, p1, RADIUS), _edge_point(p1, p0, RADIUS), line_color, LINE_W, cv2.LINE_AA)
    cv2.line(frame, _edge_point(p1, p2, RADIUS), _edge_point(p2, p1, RADIUS), line_color, LINE_W, cv2.LINE_AA)
    for p in pts:
        cv2.circle(frame, p, RADIUS, point_color, BORDER_W, cv2.LINE_AA)


def draw_skeleton_points_colored(frame, pts, colors, point_colors, line_color=None):
    """Same visual design as draw_skeleton (shoulder->elbow->wrist arm with
    edge-trimmed lines + bordered circles), but each of the 3 points can get
    its own color — e.g. wrist circle turns red at top while the rest of the
    arm stays highlighted.

    point_colors: list of 3 BGR tuples, one per point in `pts` (same order).
    line_color:   color for both line segments; defaults to white.
    """
    if len(pts) < 3:
        return
    SKEL_COLOR = (255, 255, 255)
    line_color = line_color if line_color is not None else SKEL_COLOR
    LINE_W = 5
    RADIUS = 12
    BORDER_W = 8
    def _edge_point(src, dst, r):
        dx, dy = dst[0] - src[0], dst[1] - src[1]
        dist = math.hypot(dx, dy)
        if dist < 1:
            return src
        return (int(src[0] + dx / dist * r), int(src[1] + dy / dist * r))
    p0, p1, p2 = pts[0], pts[1], pts[2]
    cv2.line(frame, _edge_point(p0, p1, RADIUS), _edge_point(p1, p0, RADIUS), line_color, LINE_W, cv2.LINE_AA)
    cv2.line(frame, _edge_point(p1, p2, RADIUS), _edge_point(p2, p1, RADIUS), line_color, LINE_W, cv2.LINE_AA)
    for p, pc in zip(pts, point_colors):
        cv2.circle(frame, p, RADIUS, pc if pc is not None else SKEL_COLOR, BORDER_W, cv2.LINE_AA)


def draw_stats(
    frame,
    *,
    exercise_name: str,
    reps: int,
    good_reps: int,
    bad_reps: int,
    current_rep: str,
    stage: str,
    angle: float | None,
    feedback: list[str] | None = None,
    colors,
):
    """Draw the stats overlay - FIXED SIZE, WRAPS LONG TEXT.

    - Fixed width 400px, fixed height 9 lines (compact)
    - Long messages wrap to next line instead of ... 
    - Max 2 feedback messages to keep box small
    - No jumping - box size never changes
    """
    h, w = frame.shape[:2]
    feedback = feedback or []
    display_feedback = feedback[:STATS_MAX_FEEDBACK]

    # Core 7 lines
    core_lines = [
        exercise_name,
        f"Total Reps : {reps}",
        f"Good Reps  : {good_reps}",
        f"Bad Reps   : {bad_reps}",
        f"Current Rep: {current_rep}",
        f"Stage      : {stage}",
        f"Angle      : {int(angle)} deg" if angle is not None else "Angle: N/A",
    ]

    def wrap_text(text: str, max_width_px: int, indent: str = "") -> list[str]:
        """Wrap text into multiple lines that fit max_width."""
        if not text.strip():
            return [text]
        # Check if fits in one line
        (tw, _), _ = cv2.getTextSize(text, STATS_FONT, STATS_FONT_SCALE, STATS_THICKNESS), 0
        size = cv2.getTextSize(text, STATS_FONT, STATS_FONT_SCALE, STATS_THICKNESS)[0]
        if size[0] <= max_width_px:
            return [text]
        # Split into words and wrap
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            sw = cv2.getTextSize(test, STATS_FONT, STATS_FONT_SCALE, STATS_THICKNESS)[0][0]
            if sw <= max_width_px:
                current = test
            else:
                if current:
                    lines.append(current)
                    # For feedback, indent continuation lines
                    current = indent + word if indent else word
                else:
                    # Single word longer than max - force it (will overflow slightly)
                    lines.append(word)
                    current = indent if indent else ""
        if current:
            lines.append(current)
        return lines

    # Build final wrapped lines
    final_lines = []
    for line in core_lines:
        final_lines.extend(wrap_text(line, STATS_MAX_TEXT_WIDTH))

    # Wrap feedback with "- " prefix on first line, "  " indent on continuation
    for msg in display_feedback:
        prefixed = f"- {msg}"
        wrapped = wrap_text(prefixed, STATS_MAX_TEXT_WIDTH, indent="  ")
        final_lines.extend(wrapped)

    # Trim to max lines and pad to keep fixed height
    final_lines = final_lines[:STATS_MAX_LINES]
    while len(final_lines) < STATS_MAX_LINES:
        final_lines.append("")

    def line_color(text: str):
        if text.startswith("- ") or text.startswith("  "):
            return colors.ERROR
        if text.startswith("Current Rep:"):
            return colors.ERROR if "BAD" in text else colors.HIGHLIGHT
        return colors.TEXT

    box_width = STATS_FIXED_WIDTH
    box_height = STATS_FIXED_HEIGHT
    box_x = STATS_MARGIN
    box_y = h - STATS_MARGIN - box_height
    box_x = max(STATS_MARGIN, min(box_x, w - STATS_MARGIN - box_width))
    box_y = max(STATS_MARGIN, min(box_y, h - STATS_MARGIN - box_height))

    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, STATS_BG_ALPHA, frame, 1 - STATS_BG_ALPHA, 0, frame)

    for i, text in enumerate(final_lines):
        if i >= STATS_MAX_LINES:
            break
        # Skip color check for indented continuation lines - keep ERROR color if original was error
        base_text = text.lstrip()
        col = colors.ERROR if text.startswith("  ") or text.startswith("- ") else line_color(text)
        cv2.putText(
            frame, text,
            (box_x + STATS_PADDING, box_y + STATS_PADDING + (i + 1) * STATS_LINE_HEIGHT - 4),
            STATS_FONT, STATS_FONT_SCALE, col, STATS_THICKNESS, cv2.LINE_AA,
        )


# ── Screen-fit display ──────────────────────────────────────────────────────
SCREEN_MARGIN_RATIO = 0.05
SCREEN_MARGIN_PX = 50
DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 720


@functools.lru_cache(maxsize=1)
def get_screen_size():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        if w > 0 and h > 0:
            return (w, h)
    except Exception:
        pass
    return (DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)


def fit_to_screen(frame, max_width=None,
                  margin_ratio=SCREEN_MARGIN_RATIO, margin_px=SCREEN_MARGIN_PX):
    screen_w, screen_h = get_screen_size()
    margin_x = max(int(screen_w * margin_ratio), margin_px)
    margin_y = max(int(screen_h * margin_ratio), margin_px)
    avail_w = max(1, screen_w - 2 * margin_x)
    avail_h = max(1, screen_h - 2 * margin_y)
    h, w = frame.shape[:2]
    caps = [avail_w / w, avail_h / h, 1.0]
    if max_width is not None:
        caps.append(max_width / w)
    scale = min(caps)
    if scale >= 1.0:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def draw_angle_arc(frame, a, b, c, colors, is_bad=False, radius=20):
    ARC_RADIUS = 42
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    angle1 = math.degrees(math.atan2(ba[1], ba[0]))
    angle2 = math.degrees(math.atan2(bc[1], bc[0]))
    start_angle = int(angle1)
    end_angle = int(angle2)
    if end_angle < start_angle:
        end_angle += 360
    if end_angle - start_angle > 180:
        start_angle, end_angle = end_angle, start_angle + 360
    color = colors.ERROR if is_bad else colors.HIGHLIGHT
    cv2.ellipse(frame, b, (ARC_RADIUS, ARC_RADIUS), 0, start_angle, end_angle, color, 2, cv2.LINE_AA)


ANGLE_FONT = cv2.FONT_HERSHEY_SIMPLEX
ANGLE_BASE_SCALE = 0.9
ANGLE_PADDING = 6
ANGLE_OFFSET = 14
ANGLE_BG_ALPHA = 0.65
ANGLE_MIN_SCALE = 0.7
ANGLE_MAX_SCALE = 2.0


def _angle_scale(width: int) -> float:
    return max(ANGLE_MIN_SCALE, min(ANGLE_MAX_SCALE, width / 1280.0))


def draw_angle_labels(frame, views: list[ComputedAngle], colors, width: int, height: int):
    scale = _angle_scale(width)
    font_scale = ANGLE_BASE_SCALE * scale
    thickness = max(1, round(2 * scale))
    padding = round(ANGLE_PADDING * scale)
    offset = round(ANGLE_OFFSET * scale)
    border = max(1, round(2 * scale))
    for v in views:
        if v.angle is None:
            continue
        # Skip labels whose vertex landed at the top-left corner — this happens
        # when the landmark could not be found (get_points returns empty list and
        # the engine falls back to (0, 0)). Rendering there creates a confusing
        # "0 deg" / "2 deg" box that has nothing to do with the exercise.
        if v.vertex == (0, 0):
            continue
        color = colors.ERROR if v.is_error else colors.HIGHLIGHT
        text = f"{int(round(v.angle))} deg"
        (tw, th), _ = cv2.getTextSize(text, ANGLE_FONT, font_scale, thickness)
        box_w = tw + padding * 2
        box_h = th + padding * 2
        bx = v.vertex[0] + offset
        by = v.vertex[1] - offset - box_h
        bx = max(0, min(bx, width - box_w))
        by = max(0, min(by, height - box_h))
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, by), (bx + box_w, by + box_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, ANGLE_BG_ALPHA, frame, 1 - ANGLE_BG_ALPHA, 0, frame)
        cv2.rectangle(frame, (bx, by), (bx + box_w, by + box_h), color, border)
        cv2.putText(frame, text, (bx + padding, by + padding + th), ANGLE_FONT, font_scale, color, thickness, cv2.LINE_AA)


def draw_segment_line(frame, pt1, pt2, colors, custom_color=None):
    line_color = custom_color if custom_color is not None else colors.HIGHLIGHT
    cv2.line(frame, pt1, pt2, line_color, 3, cv2.LINE_AA)


def draw_wrist_line(frame, left_wrist, right_wrist, colors, custom_color=None):
    draw_segment_line(frame, left_wrist, right_wrist, colors, custom_color)


def draw_countdown_overlay(frame, seconds_left: int, colors):
    """Draw a beautiful countdown timer overlay at the start of the exercise."""
    h, w = frame.shape[:2]
    # Draw dark semi-transparent overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    # Circle properties
    center_x, center_y = w // 2, h // 2
    circle_radius = 80
    circle_color = colors.HIGHLIGHT
    circle_thickness = 6

    # Draw central circle
    cv2.circle(frame, (center_x, center_y), circle_radius, circle_color, circle_thickness, cv2.LINE_AA)

    # Draw the countdown number inside the circle
    text_num = str(seconds_left)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2.5
    thickness = 6
    (tw, th), _ = cv2.getTextSize(text_num, font, font_scale, thickness)
    tx = center_x - tw // 2
    ty = center_y + th // 2
    cv2.putText(frame, text_num, (tx, ty), font, font_scale, colors.TEXT, thickness, cv2.LINE_AA)

    # Draw message: "TAKE YOUR POSITION" above
    text_msg1 = "TAKE YOUR POSITION"
    font_scale_msg = 0.9
    thickness_msg = 2
    (tw1, th1), _ = cv2.getTextSize(text_msg1, font, font_scale_msg, thickness_msg)
    tx1 = center_x - tw1 // 2
    ty1 = center_y - circle_radius - 35
    cv2.putText(frame, text_msg1, (tx1, ty1), font, font_scale_msg, colors.HIGHLIGHT, thickness_msg, cv2.LINE_AA)

    # Draw message: "GET READY..." below
    text_msg2 = "GET READY..."
    (tw2, th2), _ = cv2.getTextSize(text_msg2, font, font_scale_msg, thickness_msg)
    tx2 = center_x - tw2 // 2
    ty2 = center_y + circle_radius + 50
    cv2.putText(frame, text_msg2, (tx2, ty2), font, font_scale_msg, colors.TEXT, thickness_msg, cv2.LINE_AA)



def draw_midline(frame, shoulder_pts, hip_pts, colors, custom_color=None):
    """Draw a line from the shoulder midpoint to the hip midpoint with center point."""
    if len(shoulder_pts) < 2 or len(hip_pts) < 2:
        return
    sx = int(sum(p[0] for p in shoulder_pts) / len(shoulder_pts))
    sy = int(sum(p[1] for p in shoulder_pts) / len(shoulder_pts))
    hx = int(sum(p[0] for p in hip_pts) / len(hip_pts))
    hy = int(sum(p[1] for p in hip_pts) / len(hip_pts))
    
    # Use white color for the line (standard design like other exercises)
    color = custom_color if custom_color is not None else (255, 255, 255)
    
    # Draw vertical line
    cv2.line(frame, (sx, sy), (hx, hy), color, 2, cv2.LINE_AA)
    
    # Draw center point on the vertical line
    cx = (sx + hx) // 2
    cy = (sy + hy) // 2
    cv2.circle(frame, (cx, cy), 6, color, -1, cv2.LINE_AA)


def draw_startup_overlay(frame, message: str, in_position: bool, colors, seconds_left: float = None):
    """Draw a status bar at the top of the frame for the startup position hold check."""
    h, w = frame.shape[:2]
    
    # Semi-transparent bar at the top
    bar_height = 70
    overlay = frame.copy()
    
    # Background color: green if in position, orange/red if not
    bg_color = (0, 100, 0) if in_position else (0, 0, 150)  # BGR
    
    cv2.rectangle(overlay, (0, 0), (w, bar_height), bg_color, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    
    if in_position and seconds_left is not None:
        text = f"{message} (Ready in {seconds_left:.1f}s)"
        text_color = (100, 255, 100)  # bright green
    else:
        text = message
        text_color = (255, 255, 255)  # white
        
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    tx = (w - tw) // 2
    ty = (bar_height + th) // 2
    
    cv2.putText(frame, text, (tx, ty), font, font_scale, text_color, thickness, cv2.LINE_AA)