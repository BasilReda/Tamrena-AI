"""Upright Row exercise configuration (self-contained).

Both arms tracked simultaneously, full 3D (Camera.BOTH) — not single-side.

Counting — vertical POSITION, not a joint angle:
    A virtual vertical line runs from the shoulder midpoint (avg L/R
    shoulder) down to the hip midpoint (avg L/R hip). The wrists' average
    height is expressed as a ratio t along that line:
        t = 0.0  -> wrists at hip level        (bottom / rest)
        t = 0.5  -> wrists at the line's CENTER point (torso midpoint)
        t = 1.0  -> wrists at shoulder level    (top)
    A rep completes when wrists rise from hip level, cross the center
    point (t > up_angle), reach shoulder level (t >= max_rom_angle), then
    return to hip level (t <= down_angle).

Validation:
    Grip-proximity is INFO severity only -> shown as a message and turns
    the arm lines red, but per spec it never affects good/bad. The actual
    good/bad call comes purely from the vertical ROM thresholds above
    (reaching hip level at bottom AND shoulder level at top).

Display:
    Hip line, shoulder line, the virtual center line, and arms drawn
    wrist -> elbow only. No angle arcs, no angle-degree labels.
"""

from dataclasses import dataclass, field

from ..core.pose_segments import (
    L_SHOULDER, R_SHOULDER, L_ELBOW, R_ELBOW, L_WRIST, R_WRIST, L_HIP, R_HIP,
)
from .exercise import Camera, DisplaySettings, Exercise, ExerciseMetadata, SegmentLine
from .rules import VerticalPositionCounterRule, DistanceValidationRule, Severity


@dataclass
class UprightRowExercise(Exercise):
    name: str = "Upright Row"
    camera: Camera = Camera.BOTH
    use_3d: bool | None = True

    counter_rules: list = field(
        default_factory=lambda: [
            VerticalPositionCounterRule(
                name="upright_row",
                points=(L_WRIST, R_WRIST),
                shoulder_landmarks=(L_SHOULDER, R_SHOULDER),
                hip_landmarks=(L_HIP, R_HIP),
                up_angle=0.3,        # crossing above center point starts the "up" attempt
                down_angle=0.1,      # back near hip level = rest / DOWN
                min_rom_angle=None,   # no ROM check at bottom
                max_rom_angle=None,   # no ROM check at top - good/bad determined by wrist proximity only
                stability_frames=1,  # very short - upright row reverses fast
            ),
        ]
    )

    validation_rules: list = field(
        default_factory=lambda: [
            # Grip too narrow → BAD rep.  ERROR severity = poisons reps when wrists
            # are closer than shoulder width (ratio < 1.0).
            DistanceValidationRule(
                name="upright_row_wrist_proximity",
                measurement=(L_WRIST, R_WRIST),
                reference=(L_SHOULDER, R_SHOULDER),
                min_ratio=1.0,   # wrists must be at least as wide as shoulders
                max_ratio=5.0,
                message="Wrists too close — widen your grip",
                severity=Severity.ERROR,  # ERROR = marks rep as BAD
            ),
        ]
    )

    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(
            show_skeleton=True,            # Use the same circle+line design as other exercises
            show_validation_skeleton=False,
            show_angle_arc=False,          # No angle arcs — this exercise has no angle validation
            show_angle_labels=False,       # No angle degree labels — no angles here at all
            show_center_line=True,         # Keep the vertical shoulder-mid -> hip-mid guide line
            segment_lines=[],
        )
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Vertical pulling exercise for the shoulders and traps.",
            muscle_groups=("shoulders", "trapezius", "biceps"),
        )
    )