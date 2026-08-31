"""Live coaching session runner — NOW FULL 3D.

Streams an engine session over a queue:
- Analysis: 3D world landmarks (camera independent)
- Rendering: 2D image landmarks (screen space)
"""

import queue
import threading
import time
from typing import Any, Dict, List, Optional

import cv2

from ..config import RENDERED_DIR, settings
from ..exercises.exercise import Camera
from ..exercises.rules import Severity
from ..exercises.validation import violations
from ..services.gym_engine import GymEngine
from ..services.video_source import VideoSourceError, open_capture
from ..services.pose_service import PoseService
from ..utils.render import fit_to_screen

_STATE_EVERY_N_FRAMES = 2
_STREAM_MAX_WIDTH = 960
_JPEG_QUALITY = 70
_DEFAULT_WEIGHTS = {"error": 50.0, "warning": 20.0, "info": 10.0}


class LiveSession(threading.Thread):

    def __init__(
        self,
        exercise: str,
        source: str,
        events: "queue.Queue",
        video_path: Optional[str] = None,
        use_3d: bool | None = None,
        frame_queue: Optional["queue.Queue"] = None,
    ) -> None:
        super().__init__(daemon=True)
        self.exercise_key = exercise
        self.source = source
        self.video_path = video_path
        self.events = events
        self.frame_queue = frame_queue
        # If not specified, use from settings/.env
        self.use_3d = use_3d if use_3d is not None else settings.USE_3D
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def _publish(self, event) -> None:
        try:
            self.events.put_nowait(event)
        except queue.Full:
            try:
                self.events.get_nowait()
            except queue.Empty:
                pass
            try:
                self.events.put_nowait(event)
            except queue.Full:
                pass

    @staticmethod
    def _live_score(results, weights) -> Optional[float]:
        penalty = sum(weights.get(r.severity, weights.get(str(r.severity), 0.0))
                      for r in results if not r.passed)
        return max(0.0, 100.0 - penalty)

    def _state(self, engine: GymEngine, results, elapsed: float, fps: float) -> Dict[str, Any]:
        primary = engine.counter.primary
        last = engine.judge.last_rep
        rule = engine.exercise.counter_rules[0] if engine.exercise.counter_rules else None
        stage_map = {
            "up": getattr(rule, "up_stage", "up"),
            "down": getattr(rule, "down_stage", "down"),
        }
        failing = violations(results)
        return {
            "type": "state",
            "exercise": engine.exercise.name,
            "elapsed": round(elapsed, 1),
            "fps": round(fps, 1),
            "reps": engine.counter.primary.count,
            "good": engine.judge.good_reps,
            "bad": engine.judge.bad_reps,
            "stage": stage_map.get(primary.stage, primary.stage),
            "angle": round(primary.angle, 1) if primary.angle else 0,
            "last_rep": ("good" if last.good else "bad") if last else None,
            "live_score": self._live_score(results, _DEFAULT_WEIGHTS),
            "side": (engine.side_detector.detected_side if engine.side_detector else "both"),
            "adapting": not engine.rules_adapted,
            "is_3d": engine.use_3d,
            "feedback": [r.message for r in failing][:3],
            "rules": [
                {
                    "name": r.rule_name,
                    "passed": r.passed,
                    "severity": str(getattr(r.severity, "value", r.severity)),
                    "message": r.message,
                    "value": round(r.angle, 1) if r.angle is not None else None,
                    "is_3d": getattr(r, 'is_3d', True)
                }
                for r in results
            ],
        }

    def run(self) -> None:
        import numpy as np
        from ..exercises.registry import registry

        try:
            engine = GymEngine(registry.get(self.exercise_key), use_3d=self.use_3d, smooth=True)
        except Exception as exc:
            self._publish({"type": "error", "message": f"Unknown exercise: {exc}"})
            return

        cap = None
        if self.source != "browser":
            try:
                cap = open_capture(
                    video_path=self.video_path
                    or (str(settings.VIDEO_PATH) if settings.VIDEO_PATH else None),
                    use_webcam=self.source == "webcam",
                    webcam_index=settings.WEBCAM_INDEX,
                )
            except VideoSourceError as exc:
                self._publish({"type": "error", "message": str(exc)})
                return

        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in engine.exercise.name)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        writer = None
        rendered_name: Optional[str] = None
        rendered_error: Optional[str] = None

        # --- Dynamic FPS detection ---
        import math
        if cap is not None:
            detected_fps = cap.get(cv2.CAP_PROP_FPS)
            if detected_fps is None or detected_fps <= 0 or detected_fps > 120 or math.isnan(detected_fps):
                detected_fps = settings.ANALYTICS_FPS  # fallback, will be updated by live measurement
        else:
            detected_fps = settings.ANALYTICS_FPS
        fps_for_writer = detected_fps

        if settings.SAVE_OUTPUT and cap is not None:
            try:
                RENDERED_DIR.mkdir(parents=True, exist_ok=True)
                rendered_name = f"{safe_name}_{stamp}.mp4"
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(RENDERED_DIR / rendered_name), fourcc, fps_for_writer, (width, height))
                if not writer.isOpened():
                    writer.release()
                    writer, rendered_name = None, None
                    rendered_error = "OpenCV could not create the output video"
            except Exception as exc:
                writer, rendered_name = None, None
                rendered_error = str(exc)

        try:
            pose_service = PoseService(settings.MODEL_PATH)
        except Exception as exc:
            if cap is not None:
                cap.release()
            if writer is not None:
                writer.release()
                (RENDERED_DIR / rendered_name).unlink(missing_ok=True)
            self._publish({"type": "error", "message": f"Pose model unavailable: {exc}"})
            return

        fps = detected_fps
        results: List = []
        frame_id, frames_tick = 0, 0
        start = time.perf_counter()
        last_fps_check = start
        last_timestamp = -1
        live_fps = fps  # start with detected, will be measured
        # Set only when the loop exits because of the duration cap; carried
        # into the terminal "end" event below so the client learns why the
        # session stopped (never surfaced as a separate "error" event —
        # forward_events() in routes/live.py treats "error" as terminal and
        # would drop the "end" event, including the export's session_id).
        stopped_reason: Optional[str] = None

        while not self._stop.is_set():
            if time.perf_counter() - start > settings.MAX_SESSION_SECONDS:
                stopped_reason = "max_duration_exceeded"
                break

            if self.source == "browser":
                if self.frame_queue is None:
                    break
                try:
                    raw_bytes = self.frame_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if raw_bytes is None or self._stop.is_set():
                    break

                nparr = np.frombuffer(raw_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                if writer is None and settings.SAVE_OUTPUT and rendered_error is None:
                    try:
                        RENDERED_DIR.mkdir(parents=True, exist_ok=True)
                        rendered_name = f"{safe_name}_{stamp}.mp4"
                        h_init, w_init = frame.shape[:2]
                        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                        writer = cv2.VideoWriter(str(RENDERED_DIR / rendered_name), fourcc, fps_for_writer, (w_init, h_init))
                        if not writer.isOpened():
                            writer.release()
                            writer, rendered_name = None, None
                            rendered_error = "OpenCV could not create the output video"
                    except Exception as exc:
                        writer, rendered_name = None, None
                        rendered_error = str(exc)
            else:
                ok, frame = cap.read()
                if not ok:
                    break

            h, w = frame.shape[:2]
            if self.source == "browser":
                now_ts = int((time.perf_counter() - start) * 1000)
                timestamp = max(last_timestamp + 1, now_ts)
                last_timestamp = timestamp
            else:
                timestamp = int((frame_id / fps) * 1000)
            detection = pose_service.detect(frame, timestamp)
            frame_result = None
            if detection and detection.pose_landmarks:
                frame_result = engine.analyze(
                    detection.pose_landmarks, 
                    detection.world_landmarks,
                    w, h, frame_id, timestamp
                )
                results = frame_result.results
                engine._render(frame, frame_result, detection.pose_landmarks, w, h)

            if writer is not None:
                writer.write(frame)
            stream = fit_to_screen(frame, max_width=_STREAM_MAX_WIDTH)
            ok_jpg, jpg = cv2.imencode(
                ".jpg", stream, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
            )
            if ok_jpg:
                self._publish(jpg.tobytes())
            if frame_id % _STATE_EVERY_N_FRAMES == 0:
                elapsed = time.perf_counter() - start
                self._publish(self._state(engine, results, elapsed, live_fps))
            frame_id += 1
            frames_tick += 1
            now = time.perf_counter()
            if now - last_fps_check >= 1.0:
                measured = frames_tick / (now - last_fps_check)
                if measured > 0:
                    live_fps = measured
                    # Adapt fps for timestamp calculation if we were using fallback
                    if detected_fps == settings.ANALYTICS_FPS:
                        fps = (fps * 0.7 + live_fps * 0.3)
                frames_tick, last_fps_check = 0, now

        if cap is not None:
            cap.release()
        if writer is not None:
            writer.release()

        elapsed = time.perf_counter() - start
        # Use final measured fps for report if available
        final_fps = live_fps if live_fps > 0 else fps
        ended: Dict[str, Any] = {"type": "end", "reps": engine.judge.total_reps, "is_3d": engine.use_3d, "fps": round(final_fps, 1)}
        if rendered_name is not None:
            ended["rendered_video"] = rendered_name
        if rendered_error is not None:
            ended["rendered_error"] = rendered_error
        if stopped_reason:
            ended["stopped_reason"] = stopped_reason
        try:
            from ..analytics.analyzer import SessionAnalyzer
            from ..analytics.exporters import JsonSessionExporter

            report = SessionAnalyzer().build_report(
                engine.judge.history,
                exercise=engine.exercise,
                fps=final_fps,
                total_duration=elapsed,
            )
            settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
            out = JsonSessionExporter().export(report, target)
            ended["session_id"] = report.session.id if report.session else out.stem
        except Exception as exc:
            ended["export_error"] = str(exc)
        self._publish(ended)
