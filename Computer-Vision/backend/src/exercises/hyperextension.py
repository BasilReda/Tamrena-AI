"""
Hyperextension Exercise - Lower Back Focus

This exercise targets the lower back by extending the torso while keeping
a neutral spine. The goal is to reach parallel with the legs (170-180°)
without hyperextending/arching the back (>190°).

Movement Pattern:
  - Bottom: ~90-110° (torso hinged down at hips)
  - Top: 170-180° (torso aligned straight with legs)
  - Error: >190° (back arches backward excessively)

Camera: SIDE view
"""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, DisplaySettings, Exercise
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class HyperextensionExercise(Exercise):
    name: str = "Hyperextension"
    camera: str = "SIDE"
    use_3d: bool | None = True

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="hip_extension",
                joints=PoseSegments.LEFT_LEG,   # Shoulder → Hip → Knee
                up_angle=170,                   # crossing above 170° -> UP stage
                down_angle=110,                 # crossing below 110° -> DOWN stage
                up_stage="up",
                down_stage="down",
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="back_arch",
                joints=PoseSegments.LEFT_LEG,   # Shoulder → Hip → Knee
                min_angle=0,
                max_angle=190,                  # warn if > 190° (hyperextension)
                message="Stop arching your back! Keep your spine straight.",
                severity=Severity.WARNING,
            ),
        ]
    )

    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(
            show_skeleton=True,
            show_angle_arc=True,
        )
    )
