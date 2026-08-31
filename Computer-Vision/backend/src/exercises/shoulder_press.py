"""Shoulder Press exercise configuration (self-contained).

Rep counting:
  Reps are ONLY counted when both wrists are above the shoulder level at the
  start (startup validation gate, handled in gym_engine).
  One rep = arms UP (elbows >90°) → DOWN (elbows <90°) → back to UP.

Elbow flare:
  Elbows should stay within ~160° max when pressing.  If one arm flares past
  160° that joint circle turns red (warning only).  If BOTH flare the whole
  rep is poisoned as BAD.
"""

from dataclasses import dataclass, field

from ..core.pose_segments import L_SHOULDER, R_SHOULDER, L_WRIST, R_WRIST, PoseSegments
from .exercise import Camera, DisplaySettings, Exercise, ExerciseMetadata, SegmentLine
from .rules import (
    AngleCounterRule,
    AngleValidationRule,
    AngleROMValidationRule,
    DistanceValidationRule,
    Severity,
)


@dataclass
class ShoulderPressExercise(Exercise):
    name: str = "Shoulder Press"
    camera: Camera = Camera.BOTH
    use_3d: bool | None = False  # Set to False by default as requested

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            # Use elbow angles for stage detection (up/down)
            # Stage changes at 90°: >90 = up, <90 = down
            # Using LEFT_ARM (shoulder-elbow-wrist) so only arm points are shown in skeleton
            AngleCounterRule(
                name="left_shoulder",
                joints=PoseSegments.LEFT_ARM,
                up_angle=91,   # Trigger up stage when > 90
                down_angle=89,  # Trigger down stage when < 90
                sync_group="shoulder_press",
                min_rep_frames=5,  # Force CustomCounterHelper routing to count reps up->down->up correctly
            ),
            AngleCounterRule(
                name="right_shoulder",
                joints=PoseSegments.RIGHT_ARM,
                up_angle=91,   # Trigger up stage when > 90
                down_angle=89,  # Trigger down stage when < 90
                sync_group="shoulder_press",
                min_rep_frames=5,
            ),
        ]
    )
    validation_rules: list = field(
        default_factory=lambda: [
            # ROM validation for shoulder angles
            AngleROMValidationRule(
                name="left_shoulder_rom",
                joints=PoseSegments.LEFT_ARM_DIRECTION,
                min_rom_angle=40,
                max_rom_angle=160,
                message="Shoulder: Reach 160° up, 40-80° down",
                severity=Severity.ERROR,
            ),
            AngleROMValidationRule(
                name="right_shoulder_rom",
                joints=PoseSegments.RIGHT_ARM_DIRECTION,
                min_rom_angle=40,
                max_rom_angle=160,
                message="Shoulder: Reach 160° up, 40-80° down",
                severity=Severity.ERROR,
            ),
            # ROM validation for elbow angles
            AngleROMValidationRule(
                name="left_elbow_rom",
                joints=PoseSegments.LEFT_ARM,
                min_rom_angle=70,
                max_rom_angle=165,
                message="Elbow: Reach 165° up, 70° down",
                severity=Severity.WARNING,
            ),
            AngleROMValidationRule(
                name="right_elbow_rom",
                joints=PoseSegments.RIGHT_ARM,
                min_rom_angle=70,
                max_rom_angle=165,
                message="Elbow: Reach 165° up, 70° down",
                severity=Severity.WARNING,
            ),
            # Distance validation: wrists should be at least shoulder-width apart
            # Name starts with counter rule name to auto-poison reps
            DistanceValidationRule(
                name="left_shoulder_wrist_distance",
                measurement=(L_WRIST, R_WRIST),      # wrist span being checked
                reference=(L_SHOULDER, R_SHOULDER),  # normalized to shoulder width
                min_ratio=1.2,  # Must be at least 1.2x shoulder width (stricter)
                max_ratio=3.0,
                message="Keep wrists wider than shoulders",
                severity=Severity.ERROR,
            ),
            # Elbow flare: elbows should not open too wide (> 160°) during the press.
            # WARNING severity = poisons the rep as BAD only when BOTH arms violate.
            # In the renderer: if only ONE arm violates, only that elbow joint turns red.
            AngleValidationRule(
                name="left_elbow_flare",
                joints=PoseSegments.LEFT_ARM,  # Shoulder → Elbow → Wrist
                min_angle=0,
                max_angle=160,
                message="Keep your elbows not too wide",
                severity=Severity.WARNING,
            ),
            AngleValidationRule(
                name="right_elbow_flare",
                joints=PoseSegments.RIGHT_ARM,
                min_angle=0,
                max_angle=160,
                message="Keep your elbows not too wide",
                severity=Severity.WARNING,
            ),
        ]
    )
    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(
            # Only arm (counter) skeletons — ROM-validation joints are the same
            # arms, so drawing them adds visual noise.
            show_validation_skeleton=False,
            segment_lines=[
                # Wrist-to-wrist line while both arms are overhead; turns red
                # when the wrist-distance rule is failing.
                SegmentLine(
                    endpoints=(L_WRIST, R_WRIST),
                    active_angles=("left_shoulder", "right_shoulder"),
                    min_angle=90,
                    error_rule="left_shoulder_wrist_distance",
                ),
            ],
        )
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Overhead pressing exercise for the shoulders.",
            muscle_groups=("shoulders", "triceps", "upper chest"),
        )
    )
