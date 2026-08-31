"""Generic, exercise-agnostic training engine - NOW FULL 3D.

Key change: Analysis uses 3D world landmarks (camera independent), 
Rendering uses 2D image landmarks (screen space).

GymEngine knows NOTHING about specific exercises. Its job is:
detect pose -> 3D angle calculation -> validation in 3D -> render in 2D
"""

import datetime
import time

import cv2

from ..config import settings
from ..core import Colors
from ..exercises.exercise import Camera, Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..exercises.rules import DistanceValidationRule, Severity, Stage
from ..utils.geometry import ComputedAngle, calc_angle, calc_angle_3d, get_points, get_points_3d
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_skeleton_points_colored, draw_stats, fit_to_screen, draw_segment_line, draw_countdown_overlay, draw_midline, draw_startup_overlay
from ..utils.camera_side import CameraSideDetector
from ..utils.filters import WorldLandmarkSmoother
from .pose_service import PoseService
from .rep_counter import RepCounter
from .rep_judge import RepJudge
from .video_source import open_capture
from ..utils.geometry import ComputedAngle, calc_angle, calc_angle_3d, calc_vertical_ratio, get_points, get_points_3d

class FrameResult:
    """Everything computed for a single frame, handed to the renderer."""

    def __init__(self, angles, states, results, views=None, is_3d=True):
        self.angles = angles  # Now 3D angles
        self.states = states
        self.results: list[ValidationResult] = results
        self.views: list[ComputedAngle] = views or []
        self.is_3d = is_3d


class GymEngine:
    """
    Runs any exercise - NOW FULL 3D MODE.
    
    Analysis: 3D world landmarks (meters) -> true body angles, camera independent
    Rendering: 2D image landmarks (pixels) -> skeleton drawn on screen
    """

    def __init__(self, exercise: Exercise, colors: Colors | None = None, display_width: int = 1280, use_3d: bool | None = None, smooth: bool | None = None):
        self.exercise = exercise
        self.counter = RepCounter(exercise.counter_rules)
        self.judge = RepJudge()
        self.colors = colors or Colors()
        self.display_width = display_width
        # Per-exercise use_3d overrides the global setting; None → read from .env
        if use_3d is not None:
            self.use_3d = use_3d
        elif exercise.use_3d is not None:
            self.use_3d = exercise.use_3d
        else:
            self.use_3d = settings.USE_3D
        self.smooth_enabled = smooth if smooth is not None else settings.ENABLE_SMOOTHING
        
        # 3D Smoother for world landmarks (reduces z jitter)
        self.smoother = WorldLandmarkSmoother(min_cutoff=1.2, beta=0.02) if smooth else None
        
        self.side_detector = CameraSideDetector(30) if exercise.camera == Camera.SIDE else None
        self.rules_adapted = False if exercise.camera == Camera.SIDE else True
        
        self._distance_rule_names = {
            r.name for r in exercise.validation_rules
            if isinstance(r, DistanceValidationRule) and r.severity != Severity.INFO
        }

        self._distance_violation_in_current_rep = False
        self._distance_violation_results = {}

        # Startup validation state
        self.ready_position_start_time = None
        
        # Enable startup validation ONLY for Leg Press and Shoulder Press
        # when running in webcam OR when settings.FORCE_TIMER_VALIDATION is True
        needs_startup_validation = (self.exercise.name in ("Leg Press", "Shoulder Press"))
        is_validation_enabled = (settings.USE_WEBCAM or getattr(settings, "FORCE_TIMER_VALIDATION", False))
        
        if needs_startup_validation and is_validation_enabled:
            self.startup_validated = False
        else:
            self.startup_validated = True

    # ------------------------------------------------------------------
    # Analysis: FULL 3D - pure logic, no I/O
    # ------------------------------------------------------------------
    def analyze(self, image_landmarks, world_landmarks=None, width: int = 1000, height: int = 1000, frame: int = 0, timestamp_ms: int = None, skip_counting: bool = False) -> FrameResult:
        """
        Compute 3D angles, update counter, run validation in 3D.
        Backward compatible with old 2D signature: analyze(landmarks, width, height, frame)
        
        Args:
            image_landmarks: 2D landmarks for rendering (x,y normalized) - or old single landmarks
            world_landmarks: 3D world landmarks (x,y,z in meters) for analysis, or width in old API
            width, height: frame dimensions for 2D projection
            frame: frame number
            timestamp_ms: timestamp for smoother
        """
        # Backward compatibility: old signature analyze(landmarks, width, height, frame)
        if isinstance(world_landmarks, int):
            # Shift args: world_landmarks is actually width
            frame = height
            height = width
            width = world_landmarks
            world_landmarks = None  # No world in old API, will fallback to 2D
        
        # If world_landmarks is actually a landmark list but is None for image, handle
        if world_landmarks is None and image_landmarks is not None:
            try:
                if image_landmarks and hasattr(image_landmarks[0], 'z'):
                    world_landmarks = image_landmarks
            except (IndexError, AttributeError, TypeError):
                pass
        # Side detection still uses 2D visibility (most reliable)
        if self.side_detector and not self.rules_adapted:
            side = self.side_detector.process_frame(image_landmarks)
            if side:
                from ..utils.camera_side import adapt_rules
                self.exercise.counter_rules = adapt_rules(self.exercise.counter_rules, side)
                self.exercise.validation_rules = adapt_rules(self.exercise.validation_rules, side)
                self.counter = RepCounter(self.exercise.counter_rules)
                self.rules_adapted = True
            if not self.rules_adapted:
                return FrameResult(angles={}, states=self.counter.states, results=[], views=[], is_3d=self.use_3d)

        # Optional smoothing for world landmarks (critical for 3D stability)
        if self.smoother and world_landmarks is not None:
            world_landmarks = self.smoother.smooth(world_landmarks, timestamp_ms)

        angles = {}
        views = []

            # ---- 3D Rep Counting ----
        for rule in self.exercise.counter_rules:
                angle = None
                pts_2d = []

                if hasattr(rule, "joints"):
                    # Existing AngleCounterRule path
                    if self.use_3d and world_landmarks is not None:
                        pts_3d = get_points_3d(rule.joints, world_landmarks)
                        if len(pts_3d) >= 3:
                            angle = calc_angle_3d(*pts_3d)

                    pts_2d = get_points(rule.joints, image_landmarks, width, height)
                    if angle is None and len(pts_2d) >= 3:
                        angle = calc_angle(*pts_2d)

                    vertex = pts_2d[1] if len(pts_2d) >= 3 else (0, 0)
                else:
                    # VerticalPositionCounterRule path
                    if self.use_3d and world_landmarks is not None:
                        pts_3d = get_points_3d(rule.points, world_landmarks)
                        sh_3d = get_points_3d(rule.shoulder_landmarks, world_landmarks)
                        hip_3d = get_points_3d(rule.hip_landmarks, world_landmarks)
                        angle = calc_vertical_ratio(pts_3d, sh_3d, hip_3d)

                    if angle is None:
                        pts_r = get_points(rule.points, image_landmarks, width, height)
                        sh_2d = get_points(rule.shoulder_landmarks, image_landmarks, width, height)
                        hip_2d = get_points(rule.hip_landmarks, image_landmarks, width, height)
                        angle = calc_vertical_ratio(pts_r, sh_2d, hip_2d)

                    pts_2d = get_points(rule.points, image_landmarks, width, height)
                    vertex = pts_2d[0] if pts_2d else (0, 0)

                angles[rule.name] = angle
                views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False, is_3d=self.use_3d))

        # ---- 3D Validation ----
        results = validate_all(
            self.exercise.validation_rules, 
            image_landmarks, 
            world_landmarks, 
            width, height, 
            states=self.counter.states,
            use_3d=self.use_3d
        )

        # Views for validation results (vertex from 2D for rendering)
        for res in results:
            pts = get_points(res.joints, image_landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed, is_3d=res.is_3d)
            )

        # ---- Rep quality tracking ----
        if not skip_counting:
            # RepJudge collects failures and complete evaluations
            # Observe must be called every frame to collect violations for reporting
            # This collects ALL failures (ERROR, WARNING, INFO) for score calculation
            self.judge.observe(results, frame)

            # For GOOD/BAD classification, all violations (including WARNING) should make BAD
            # This matches v1 behavior where form faults mark reps as BAD
            all_violation_names = {r.rule_name for r in violations(results) if r.severity != Severity.INFO}        
            
            # Use all violations for both distance tracking and counter BAD determination
            violation_names_for_distance = all_violation_names
            violation_names_for_counter = all_violation_names
            
            prev_good  = self.counter.primary.good
            prev_count = self.counter.primary.count

            # Record already called inside observe() above - evaluations tracked

            if self._distance_rule_names & violation_names_for_distance:
                self._distance_violation_in_current_rep = True
                for r in results:
                    if not r.passed and r.rule_name in self._distance_rule_names:
                        self._distance_violation_results[r.rule_name] = r

            self.counter.update(angles, violation_names_for_counter)

            if self.counter.primary.count > prev_count:
                if self._distance_violation_in_current_rep:
                    self.judge.observe(
                        list(self._distance_violation_results.values()), frame,
                    )
                    self.judge.finalize_rep(
                        self.counter.primary.count,
                        frame,
                        force_good=False,
                    )
                    self._distance_violation_in_current_rep = False
                    self._distance_violation_results.clear()
                else:
                    rep_was_good = self.counter.primary.good > prev_good
                    if self.counter.primary.speed_warning:
                        from ..exercises.validation import ValidationResult
                        self.judge.observe([
                            ValidationResult(
                                rule_name=self.exercise.counter_rules[0].name + "_too_fast",
                                message="Too fast — control the movement",
                                severity=Severity.WARNING,
                                passed=False,
                                angle=None,
                                is_3d=self.use_3d
                            )
                        ], frame)
                    self.judge.finalize_rep(
                        self.counter.primary.count,
                        frame,
                        force_good=rep_was_good,  # Counter determines good/bad based on ROM and violations
                    )

        return FrameResult(
            angles=angles, states=self.counter.states, results=results, views=views, is_3d=self.use_3d
        )

    def _check_starting_position(self, landmarks) -> bool:
        """Check if user has taken the starting position."""
        from ..core.pose_segments import L_KNEE, L_HIP, R_KNEE, R_HIP, L_WRIST, R_WRIST, L_SHOULDER, R_SHOULDER
        
        if self.exercise.name == "Leg Press":
            # Knees higher than or equal to hips level (smaller y is higher).
            l_knee = landmarks[L_KNEE]
            l_hip = landmarks[L_HIP]
            r_knee = landmarks[R_KNEE]
            r_hip = landmarks[R_HIP]
            
            left_ok = l_knee.visibility > 0.5 and l_hip.visibility > 0.5 and l_knee.y <= l_hip.y
            right_ok = r_knee.visibility > 0.5 and r_hip.visibility > 0.5 and r_knee.y <= r_hip.y
            
            if self.side_detector and self.side_detector.detected_side:
                if self.side_detector.detected_side == "left":
                    return left_ok
                else:
                    return right_ok
            return left_ok or right_ok
            
        elif self.exercise.name == "Shoulder Press":
            # Both wrists above shoulders.
            l_wrist = landmarks[L_WRIST]
            l_shoulder = landmarks[L_SHOULDER]
            r_wrist = landmarks[R_WRIST]
            r_shoulder = landmarks[R_SHOULDER]
            
            left_ok = l_wrist.visibility > 0.5 and l_shoulder.visibility > 0.5 and l_wrist.y <= l_shoulder.y
            right_ok = r_wrist.visibility > 0.5 and r_shoulder.visibility > 0.5 and r_wrist.y <= r_shoulder.y
            
            return left_ok and right_ok
            
        return True

    # ------------------------------------------------------------------
    # Rendering: ALWAYS 2D - draws on image
    # ------------------------------------------------------------------
    def _render(self, frame, result: FrameResult, image_landmarks, width: int, height: int):
        """Rendering is ALWAYS 2D - draws skeleton on frame."""
        bad = bool(violations(result.results))
        show = self.exercise.display

        if show.show_skeleton:
            drawn_joints = set()
            for rule in self.exercise.counter_rules:
                # Handle both AngleCounterRule (joints) and VerticalPositionCounterRule (points)
                rule_points = getattr(rule, "joints", getattr(rule, "points", None))
                if rule_points is None:
                    continue
                pts = get_points(rule_points, image_landmarks, width, height)
                if len(pts) >= 3:
                    custom_color = None
                    if bad:
                        custom_color = self.colors.ERROR
                    elif hasattr(rule, 'min_rom_angle') and rule.min_rom_angle is not None:
                        state = self.counter.states.get(rule.name)
                        if state is not None:
                            if state.stage in (rule.up_stage,):
                                custom_color = None
                            elif state.reached_bottom:
                                custom_color = self.colors.HIGHLIGHT
                            else:
                                custom_color = self.colors.ERROR
                    draw_skeleton(frame, pts, self.colors, is_bad=bad, custom_color=custom_color)
                    drawn_joints.add(tuple(sorted(rule_points)))

            # Special-case: Upright Row uses VerticalPositionCounterRule (points only)
            # and thus doesn't produce 3-point joint tuples for draw_skeleton().
            # Draw both arms (shoulder->elbow->wrist) using the circle+line style.
            # Per-wrist coloring rules:
            #   • Wrist above shoulder level   → that wrist dot turns red (WARNING only)
            #   • Wrist-proximity rule failing  → wrist-to-wrist line turns red (BAD rep)
            if self.exercise.counter_rules and hasattr(self.exercise.counter_rules[0], "points") and self.exercise.name == "Upright Row":
                try:
                    from ..core.pose_segments import L_SHOULDER, R_SHOULDER, L_ELBOW, R_ELBOW, L_WRIST, R_WRIST
                except Exception:
                    L_SHOULDER = R_SHOULDER = L_ELBOW = R_ELBOW = L_WRIST = R_WRIST = None

                # Per-wrist above-shoulder check (image coords: smaller y = higher)
                l_wrist_lm  = image_landmarks[L_WRIST]  if L_WRIST  is not None else None
                l_shld_lm   = image_landmarks[L_SHOULDER] if L_SHOULDER is not None else None
                r_wrist_lm  = image_landmarks[R_WRIST]  if R_WRIST  is not None else None
                r_shld_lm   = image_landmarks[R_SHOULDER] if R_SHOULDER is not None else None

                l_wrist_above = (l_wrist_lm is not None and l_shld_lm is not None
                                 and getattr(l_wrist_lm, 'visibility', 1) > 0.5
                                 and l_wrist_lm.y < l_shld_lm.y)
                r_wrist_above = (r_wrist_lm is not None and r_shld_lm is not None
                                 and getattr(r_wrist_lm, 'visibility', 1) > 0.5
                                 and r_wrist_lm.y < r_shld_lm.y)

                l_wrist_color = self.colors.ERROR if l_wrist_above else None
                r_wrist_color = self.colors.ERROR if r_wrist_above else None

                for (shoulder, elbow, wrist), wrist_pt_color in (
                    ((L_SHOULDER, L_ELBOW, L_WRIST), l_wrist_color),
                    ((R_SHOULDER, R_ELBOW, R_WRIST), r_wrist_color),
                ):
                    if shoulder is None:
                        continue
                    pts = get_points((shoulder, elbow, wrist), image_landmarks, width, height)
                    if len(pts) == 3:
                        line_col = self.colors.ERROR if bad else None
                        draw_skeleton_points_colored(
                            frame, pts, self.colors,
                            point_colors=[None, None, wrist_pt_color],
                            line_color=line_col,
                        )

                # Draw wrist-to-wrist connector; color by grip proximity rule.
                try:
                    rule0 = self.exercise.counter_rules[0]
                except Exception:
                    rule0 = None
                state = self.counter.states.get(rule0.name) if rule0 is not None else None
                if state is not None and state.stage == Stage.DOWN:
                    failed = any(
                        r.rule_name == "upright_row_wrist_proximity" and not r.passed
                        for r in result.results
                    )
                    wrist_line_color = self.colors.ERROR if failed else self.colors.HIGHLIGHT
                    wrist_pts = get_points((L_WRIST, R_WRIST), image_landmarks, width, height)
                    if len(wrist_pts) == 2:
                        draw_segment_line(frame, wrist_pts[0], wrist_pts[1], self.colors, wrist_line_color)
            if show.show_validation_skeleton:
                for rule in self.exercise.validation_rules:
                    if hasattr(rule, 'joints'):
                        joints_key = tuple(sorted(rule.joints))
                        if joints_key not in drawn_joints:
                            pts = get_points(rule.joints, image_landmarks, width, height)
                            if len(pts) >= 3:
                                draw_skeleton(frame, pts, self.colors, is_bad=bad)
                                drawn_joints.add(joints_key)

        if show.show_angle_arc:
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, image_landmarks, width, height)
                if len(pts) >= 3:
                    draw_angle_arc(frame, pts[0], pts[1], pts[2], self.colors, is_bad=bad)

        # Labels show 3D angles but positioned at 2D vertices
        # Only draw if exercise has angle labels enabled
        if show.show_angle_labels:
            draw_angle_labels(frame, result.views, self.colors, width, height)

        for seg in show.segment_lines:
            active = all(
                (result.angles.get(name) or 0.0) >= seg.min_angle
                for name in seg.active_angles
            )
            if not active:
                continue
            failed = seg.error_rule is not None and any(
                r.rule_name == seg.error_rule and not r.passed
                for r in result.results
            )
            line_color = self.colors.ERROR if failed else self.colors.HIGHLIGHT
            pts = get_points(seg.endpoints, image_landmarks, width, height)
            if len(pts) == 2:
                draw_segment_line(frame, pts[0], pts[1], self.colors, line_color)

        if show.show_center_line and self.exercise.counter_rules:
            rule = self.exercise.counter_rules[0]
            if hasattr(rule, "shoulder_landmarks"):
                sh_pts = get_points(rule.shoulder_landmarks, image_landmarks, width, height)
                hip_pts = get_points(rule.hip_landmarks, image_landmarks, width, height)
                draw_midline(frame, sh_pts, hip_pts, self.colors)

        # ── Shoulder Press: elbow-flare per-joint coloring ──────────────────
        # If only ONE elbow flares past 160°: just that elbow circle turns red.
        # If BOTH flare: the rep is already poisoned as BAD via WARNING violations;
        # the full skeleton also turns red automatically through the `bad` flag above.
        if self.exercise.name == "Shoulder Press":
            from ..core.pose_segments import L_SHOULDER, L_ELBOW, L_WRIST, R_SHOULDER, R_ELBOW, R_WRIST
            left_flare  = any(r.rule_name == "left_elbow_flare"  and not r.passed for r in result.results)
            right_flare = any(r.rule_name == "right_elbow_flare" and not r.passed for r in result.results)
            both_flare  = left_flare and right_flare
            # Only draw per-joint highlight when exactly ONE arm flares (both-flare is already
            # covered by the red skeleton from the global `bad` flag)
            if not both_flare:
                for flare, (shoulder, elbow, wrist) in (
                    (left_flare,  (L_SHOULDER, L_ELBOW, L_WRIST)),
                    (right_flare, (R_SHOULDER, R_ELBOW, R_WRIST)),
                ):
                    if flare:
                        pts = get_points((shoulder, elbow, wrist), image_landmarks, width, height)
                        if len(pts) == 3:
                            # Draw arm skeleton with just the elbow joint in red
                            draw_skeleton_points_colored(
                                frame, pts, self.colors,
                                point_colors=[None, self.colors.ERROR, None],
                                line_color=None,
                            )


        primary = self.counter.primary
        issues = violations(result.results)
        feedback = [r.message for r in issues]
        last = self.judge.last_rep
        current_rep = (
            "GOOD" if (last is not None and last.good)
            else "BAD" if last is not None
            else "—"
        )
        # Fix stage display: show UP/DOWN only, not Stage.UP
        display_stage = primary.stage
        if self.exercise.counter_rules:
            rule = self.exercise.counter_rules[0]
            if primary.stage == Stage.UP:
                display_stage = rule.up_stage
            elif primary.stage == Stage.DOWN:
                display_stage = rule.down_stage
            elif primary.stage == Stage.RETURNING:
                display_stage = "RETURNING"
        
        # Convert enum to clean string value (UP/DOWN) - fixes "stage.UP" bug
        if hasattr(display_stage, 'value'):
            display_stage = display_stage.value
        # Clean up and uppercase for display - show UP/DOWN only
        display_stage_str = str(display_stage).upper()
        # Handle custom stage names like "open"/"close" - keep as is but uppercase
        if display_stage_str.lower() in ("up", "down", "returning"):
            display_stage_str = display_stage_str.upper()
        else:
            # For custom labels like "open", show as Title case
            display_stage_str = str(display_stage).replace("_", " ").title()

        # Check if using VerticalPositionCounterRule (not angle-based)
        # If so, don't show angle display since it's a ratio, not degrees
        is_vertical_position = hasattr(self.exercise.counter_rules[0], "points")
        display_angle = None if is_vertical_position else primary.angle
        
        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            reps=self.judge.total_reps,
            good_reps=self.judge.good_reps,
            bad_reps=self.judge.bad_reps,
            current_rep=current_rep,
            stage=display_stage_str,
            angle=display_angle,
            feedback=feedback,
            colors=self.colors,
        )

    def _export_session(self, report: "SessionReport") -> None:
        from ..analytics.exporters import JsonSessionExporter

        if settings.EXPORT_FORMAT.lower() != "json":
            print(
                f"EXPORT_FORMAT '{settings.EXPORT_FORMAT}' is no longer supported"
                " for session reports — writing JSON instead."
            )

        settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.exercise.name)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
        out_path = JsonSessionExporter().export(report, target)
        print(f"Session report exported to {out_path}")

    # ------------------------------------------------------------------
    # Orchestration: video source + 3D detection + 2D render loop
    # ------------------------------------------------------------------
    def run(self, video_path: str | None = None):
        cap = open_capture(
            video_path=video_path or settings.VIDEO_PATH,
            use_webcam=settings.USE_WEBCAM,
            webcam_index=settings.WEBCAM_INDEX,
        )

        # --- Dynamic FPS detection (fixes hardcoded 25) ---
        # For video files: use actual video FPS (30, 60, 24, etc.)
        # For webcam: FPS may be 0, fallback to ANALYTICS_FPS and measure live
        import math
        detected_fps = cap.get(cv2.CAP_PROP_FPS)
        if detected_fps is None or detected_fps <= 0 or detected_fps > 120 or math.isnan(detected_fps):
            # Webcam or video with unknown FPS - use fallback and will measure
            detected_fps = settings.ANALYTICS_FPS
            print(f"⚠️  Video FPS not detectable, using fallback {detected_fps} fps (will measure live FPS)")
        else:
            print(f"📹 Detected video FPS: {detected_fps:.2f}")

        fps = detected_fps
        writer = None
        if settings.SAVE_OUTPUT:
            settings.OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(settings.OUTPUT_PATH), fourcc, fps, (width, height))

        pose_service = PoseService(settings.MODEL_PATH)
        start_time = time.perf_counter()
        frame_id = 0
        # For webcam live FPS measurement
        live_fps = fps
        frames_tick = 0
        last_fps_check = start_time

        print(f"=== AI Gym Trainer - {'3D' if self.use_3d else '2D'} MODE - {self.exercise.name} ===")
        print(f"3D Calculation: {'ENABLED' if self.use_3d else 'DISABLED (2D fallback)'}")
        print(f"Smoothing: {'ENABLED' if self.smooth_enabled and self.use_3d else 'DISABLED'}")
        print(f"Rendering: 2D (always)")
        print(f"Using FPS: {fps:.2f} ( {'video file' if not settings.USE_WEBCAM else 'webcam fallback, measuring live'} )")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            # Use detected fps for timestamp - accurate timing
            timestamp = int((frame_id / fps) * 1000)

            is_warmup = (timestamp < 5000 and settings.USE_WEBCAM)
            
            if is_warmup:
                # Get ready phase: show countdown from 5 to 1 (only for webcam)
                seconds_left = 5 - int(timestamp / 1000)
                draw_countdown_overlay(frame, seconds_left, self.colors)
                # Keep shifting start_time so workout elapsed time starts at 0 after countdown
                start_time = time.perf_counter()
            elif not self.startup_validated:
                detection = pose_service.detect(frame, timestamp)
                in_position = False
                elapsed_hold = 0.0
                
                if detection and detection.pose_landmarks:
                    in_position = self._check_starting_position(detection.pose_landmarks)
                    
                    if in_position:
                        if self.ready_position_start_time is None:
                            self.ready_position_start_time = timestamp
                        elapsed_hold = (timestamp - self.ready_position_start_time) / 1000.0
                        if elapsed_hold >= 2.0:
                            self.startup_validated = True
                    else:
                        self.ready_position_start_time = None
                        
                    # Call analyze with skip_counting=True
                    frame_result = self.analyze(
                        detection.pose_landmarks,
                        detection.world_landmarks,
                        w, h, frame_id, timestamp,
                        skip_counting=True
                    )
                    self._render(frame, frame_result, detection.pose_landmarks, w, h)
                else:
                    self.ready_position_start_time = None
                    
                # Draw starting position / hold validation overlay if still not validated
                if not self.startup_validated:
                    if self.exercise.name == "Leg Press":
                        if in_position:
                            msg = "HOLD POSITION"
                            sec_left = max(0.0, 2.0 - elapsed_hold)
                        else:
                            msg = "TAKE RIGHT POSITION: KNEES HIGHER THAN HIPS"
                            sec_left = None
                    else:  # Shoulder Press
                        if in_position:
                            msg = "Keep your right position, Ready? Hold it!"
                            sec_left = max(0.0, 2.0 - elapsed_hold)
                        else:
                            msg = "Keep your right position, Ready?"
                            sec_left = None
                            
                    draw_startup_overlay(frame, msg, in_position, self.colors, sec_left)
                    
                # Keep shifting start_time so elapsed workout duration begins after validation is completed
                start_time = time.perf_counter()
            else:
                detection = pose_service.detect(frame, timestamp)
                if detection and detection.pose_landmarks:
                    # ── Shoulder Press active-phase wrist gate ─────────────────────
                    # Even after startup validation, if the user drops both wrists
                    # below shoulder level mid-session we skip rep counting until
                    # they raise them again (prevents phantom reps from arm-drop).
                    _sp_skip = False
                    if self.exercise.name == "Shoulder Press":
                        _sp_skip = not self._check_starting_position(detection.pose_landmarks)

                    frame_result = self.analyze(
                        detection.pose_landmarks,
                        detection.world_landmarks,
                        w, h, frame_id, timestamp,
                        skip_counting=_sp_skip,
                    )
                    self._render(frame, frame_result, detection.pose_landmarks, w, h)
                    # Show a non-intrusive hint when wrists are below shoulder level
                    if _sp_skip:
                        draw_startup_overlay(
                            frame,
                            "Raise your arms above shoulder level to start",
                            False, self.colors, None
                        )

            if writer:
                writer.write(frame)

            # Display handling - supports headless (Ubuntu server, WSL, Docker)
            try:
                display_frame = fit_to_screen(frame, max_width=self.display_width)
                if hasattr(cv2, 'imshow'):
                    cv2.imshow(f"AI Gym Trainer {'3D' if self.use_3d else '2D'} - {self.exercise.name} ({fps:.1f}fps)", display_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        print("Stopped by user (q)")
                        break
                else:
                    if frame_id % 30 == 0:
                        print(f"Processing frame {frame_id} | Reps: {self.judge.total_reps} | Angle: {self.counter.primary.angle} | FPS: {live_fps:.1f}")
            except cv2.error as e:
                if "not implemented" in str(e).lower() or "gtk" in str(e).lower() or "cocoa" in str(e).lower():
                    if frame_id == 0:
                        print("⚠️  Headless mode detected (no display available).")
                        print("   Processing without preview window...")
                        print("   - Video will be processed and report exported")
                        print(f"   - FPS: {fps:.2f} detected")
                        print("   - If SAVE_OUTPUT=true, annotated video saved to output/videos/")
                        print("   - Press Ctrl+C to stop")
                    if frame_id % 60 == 0:
                        primary = self.counter.primary
                        print(f"Frame {frame_id} | Reps: {self.judge.total_reps} (Good:{self.judge.good_reps} Bad:{self.judge.bad_reps}) | Stage: {primary.stage} | Angle: {primary.angle} | FPS: {live_fps:.1f}")
                else:
                    raise

            # Live FPS measurement for webcam (updates every second)
            frame_id += 1
            frames_tick += 1
            now = time.perf_counter()
            if now - last_fps_check >= 1.0:
                live_fps = frames_tick / (now - last_fps_check)
                frames_tick = 0
                last_fps_check = now
                # Update fps for timestamp if measuring live webcam and initial fps was fallback
                if settings.USE_WEBCAM and detected_fps == settings.ANALYTICS_FPS:
                    # Smoothly adapt to measured fps
                    fps = (fps * 0.7 + live_fps * 0.3) if live_fps > 0 else fps

        elapsed = time.perf_counter() - start_time
        frames_processed = frame_id
        # Use measured live_fps for final report if webcam, otherwise detected fps
        final_fps = live_fps if settings.USE_WEBCAM and live_fps > 0 else fps
        
        if settings.USE_WEBCAM:
            input_source = f"Webcam (index {settings.WEBCAM_INDEX}) {'3D' if self.use_3d else '2D'} @ {final_fps:.1f}fps"
        else:
            src = video_path or settings.VIDEO_PATH
            input_source = f"{str(src) if src is not None else 'none'} @ {final_fps:.1f}fps"

        print(self.judge.session_report(
            exercise_name=self.exercise.name,
            input_source=input_source,
            total_frames=frames_processed,
            elapsed_seconds=elapsed,
        ))

        if settings.EXPORT_SESSION:
            from ..analytics.analyzer import SessionAnalyzer

            report = SessionAnalyzer().build_report(
                self.judge.history,
                exercise=self.exercise,
                fps=final_fps,
                total_duration=elapsed,
            )
            self._export_session(report)

        print(f"\n{'3D' if self.use_3d else '2D'} Metrics: {self.judge.total_reps} total, {self.judge.good_reps} good, {self.judge.bad_reps} bad @ {final_fps:.1f}fps")
        print(self.judge.history)
        cap.release()
        if writer:
            writer.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass  # Headless - ignore
