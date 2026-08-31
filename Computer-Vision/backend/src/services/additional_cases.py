"""Additional cases and ROM logic helpers for RepCounter.

This module encapsulates all exercise-specific complexity (ROM, speed checks,
prefix-matched violations, sync groups) to keep the core ``rep_counter.py``
clean and simple.

It is the **single** place where stateful rep-window logic lives:
  * violation accumulation (only inside the active rep window)
  * frame-counting for minimum-speed gates
  * ROM bottom/top tracking
  * ROM-reversal with stability hysteresis (prevents noise near the top extreme
    from triggering a premature count — the key fix for leg-press-style exercises
    where the athlete may wobble slightly before truly reversing direction)
  * sync-group support (two rules that must both reach thresholds to score a rep)

No exercise names are hard-coded here.  Every behaviour is driven by the
configuration fields on :class:`AngleCounterRule`.

───────────────────────────────────────────────────────────────────────────────
MERGING HISTORY
───────────────────────────────────────────────────────────────────────────────
This file supersedes the two v1 files ``additional_cases.py`` (simple helper)
and ``additional_casses.py`` (full ROM/speed logic).  All logic from both has
been merged and extended:

  New in this file vs. v1:
    * ``_stability_counts`` — frames-above-max_rom counter that prevents the
      reversal-at-top from firing until the joint has been stable above the
      threshold for _STABILITY_FRAMES_REQUIRED consecutive frames.
    * sync-group support (carried from the v2 first pass).
    * ``state.reached_top`` tracking for the standard (non-ROM) path when
      ``max_rom_angle`` is configured there too.
"""

from typing import Dict, Optional, Set
from ..exercises.rules import AngleCounterRule, Stage


# ── Stage vocabulary ──────────────────────────────────────────────────────────
# One shared definition used by the counter, the ROM evaluator, and the engine.
STAGE_UP        = Stage.UP
STAGE_DOWN      = Stage.DOWN
STAGE_RETURNING = Stage.RETURNING

# ── Stability gate ────────────────────────────────────────────────────────────
# Minimum consecutive frames the angle must stay AT OR ABOVE max_rom_angle
# before a reversal (angle < prev_angle) can trigger a rep count.
#
# Why: sensors and pose estimation introduce noise near the top extreme.  A
# single frame where angle drops from 161° to 159° while the athlete is still
# extending should NOT trigger an early count.  Requiring 3 consecutive
# above-threshold frames filters out this 1–2-frame jitter without
# introducing perceptible lag (~100 ms at 30 fps).
#
# Set to 0 to disable (original behaviour).
_STABILITY_FRAMES_REQUIRED: int = 3


class CustomCounterHelper:
    """Handle stateful ROM, speed, violation, and sync-group logic.

    One instance is created per :class:`RepCounter` when any counter rule
    has ``max_rom_angle`` set or ``min_rep_frames > 0``.

    All per-rule tracking is keyed by ``rule.name`` so multi-rule exercises
    (e.g. both legs for leg-press, both arms for cable pulldown) are handled
    without any exercise-specific branching.
    """

    def __init__(self, counter_instance) -> None:
        self.counter = counter_instance

        # Per-rule: was there a validation violation during the current rep?
        self._pending_violations: Dict[str, bool] = {
            r.name: False for r in counter_instance.rules
        }
        # Per-rule: how many frames have elapsed since DOWN phase began?
        self._rep_frame_counts: Dict[str, int] = {
            r.name: 0 for r in counter_instance.rules
        }
        # Previous angle per rule — used for reversal detection (angle < prev)
        self._prev_angles: Dict[str, float] = {
            r.name: 0.0 for r in counter_instance.rules
        }
        # Is the current rep window open (DOWN phase started)?
        self._started: Dict[str, bool] = {
            r.name: False for r in counter_instance.rules
        }
        # How many consecutive frames has the angle been >= max_rom_angle?
        # Resets to 0 whenever angle drops below max_rom_angle.
        self._stability_counts: Dict[str, int] = {
            r.name: 0 for r in counter_instance.rules
        }
        # Per-rule: how many consecutive frames has a violation been active?
        # Used for the min_violation_frames noise-filter: a violation only poisons
        # the rep once it has persisted for at least rule.min_violation_frames frames.
        self._violation_streak: Dict[str, int] = {
            r.name: 0 for r in counter_instance.rules
        }
        # Per-rule: maximum angle observed during the current RETURNING stage.
        # Used by reversal_hysteresis to prevent wobbles from finalizing reps too early.
        self._peak_angles: Dict[str, float] = {
            r.name: 0.0 for r in counter_instance.rules
        }


        # Build sync-group index: group_name → [rule_name, ...]
        self._sync_groups: Dict[str, list[str]] = {}
        for rule in counter_instance.rules:
            if rule.sync_group:
                self._sync_groups.setdefault(rule.sync_group, []).append(rule.name)

    # ── Rep lifecycle helpers ─────────────────────────────────────────────────

    def _count_rep(
        self,
        rule: AngleCounterRule,
        state,
        *,
        good: bool,
        too_fast: bool = False,
    ) -> None:
        """Finalise one repetition and increment the counters."""
        state.count += 1
        if good:
            state.good += 1
        else:
            state.bad += 1
        self._started[rule.name]           = False
        self._stability_counts[rule.name]  = 0
        self._violation_streak[rule.name]  = 0
        state.speed_warning                = too_fast

    def _start_down(
        self,
        rule: AngleCounterRule,
        state,
        angle: float,
    ) -> None:
        """Enter DOWN phase: reset rep-window counters and begin frame tracking."""
        state.stage                            = STAGE_DOWN
        self._started[rule.name]               = True
        state.reached_bottom                   = False
        state.reached_top                      = False
        state.speed_warning                    = False
        self._pending_violations[rule.name]    = False
        self._rep_frame_counts[rule.name]      = 0
        self._stability_counts[rule.name]      = 0
        self._violation_streak[rule.name]      = 0
        self._peak_angles[rule.name]           = 0.0

        # Already at the bottom extreme on entry?
        rom_min = getattr(rule, "min_rom_angle", None)
        if rom_min is not None and angle <= rom_min:
            state.reached_bottom = True

    # ── Sync-group helpers ────────────────────────────────────────────────────

    def _check_sync_group_ready(
        self,
        rule: AngleCounterRule,
        angles: Dict[str, Optional[float]],
    ) -> bool:
        """True when all members of the sync group have an open rep window."""
        if not rule.sync_group:
            return True
        for member_name in self._sync_groups.get(rule.sync_group, []):
            if not self._started[member_name]:
                return False
        return True

    def _sync_group_count(
        self,
        rule: AngleCounterRule,
        good: bool,
        too_fast: bool,
    ) -> None:
        """Count a rep for every member of the sync group simultaneously."""
        if not rule.sync_group:
            return
        for member_name in self._sync_groups.get(rule.sync_group, []):
            member_rule  = next(r for r in self.counter.rules if r.name == member_name)
            member_state = self.counter.states[member_name]
            self._count_rep(member_rule, member_state, good=good, too_fast=too_fast)

    # ── Violation accumulation ────────────────────────────────────────────────

    def _accumulate_violations(
        self,
        rule: AngleCounterRule,
        vnames: Set[str],
    ) -> None:
        """Collect violations that belong to this rule's rep window.

        Matching strategy:
          • Any violation whose name starts with ``rule.name`` belongs to this
            rule (e.g. ``"elbow_drift"`` for rule ``"elbow"``).
          • For the *primary* counter rule (first in the list) we additionally
            collect violations that don't belong to any other counter rule —
            these are general posture checks (e.g. ``"back_straight"``).

        Accumulation only happens while the rep window is open (``_started``).
        """
        if not self._started[rule.name]:
            return

        has_rom = getattr(rule, "max_rom_angle", None) is not None

        # When this rule uses ROM tracking (max_rom_angle is set), the engine
        # also evaluates an AngleROMValidationRule with the *same* name.  That
        # rule correctly reports FAILED while the user is still returning to
        # the top extreme — which is not a form error, it is the ROM progress
        # indicator.  Exclude it here so it never poisons the rep-quality flag.
        # (Same exclusion as v1: `not (has_rom and v == rule.name)`)
        active_viols: Set[str] = {
            v for v in vnames
            if v.startswith(rule.name) and not (has_rom and v == rule.name)
        }

        if rule is self.counter.rules[0]:
            counter_rule_names = {r.name for r in self.counter.rules}
            other_viols = {
                v for v in vnames
                if not any(v.startswith(cr) for cr in counter_rule_names)
                and not (has_rom and v == rule.name)
            }
            active_viols.update(other_viols)

        if active_viols:
            # min_violation_frames gate: only poison the rep once the violation
            # has been active for at least rule.min_violation_frames consecutive
            # frames.  This filters out 1-2-frame MediaPipe jitter spikes.
            min_vf = getattr(rule, "min_violation_frames", 0)
            self._violation_streak[rule.name] += 1
            if self._violation_streak[rule.name] >= max(1, min_vf):
                self._pending_violations[rule.name] = True
        else:
            # No violations this frame: reset the streak so it must restart
            # from scratch (non-consecutive frames don't accumulate).
            self._violation_streak[rule.name] = 0

    # ── Main update ───────────────────────────────────────────────────────────

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, any]:
        """Execute stateful ROM, speed, violation, and sync-group tracking.

        Called once per frame by :class:`RepCounter`.

        Args:
            angles:          Dict mapping rule name → current angle (degrees).
                             ``None`` means the landmark was not visible this
                             frame; the rule is skipped to avoid phantom 0°.
            violation_names: Set of validation-rule names that failed this
                             frame (from the engine's violation set).

        Returns:
            The counter's ``states`` dict (same object, mutated in place).
        """
        # Skip counting during startup frames to prevent false reps
        if self.counter.frame_count < self.counter.startup_frames:
            return self.counter.states
            
        vnames = violation_names or set()

        for rule in self.counter.rules:
            angle = angles.get(rule.name)
            if angle is None:
                # Landmark not visible — do not treat None as 0°.
                continue

            state      = self.counter.states[rule.name]
            prev_angle = self._prev_angles[rule.name]
            self._prev_angles[rule.name] = angle
            state.angle = angle

            has_rom = getattr(rule, "max_rom_angle", None) is not None

            # ── Violation accumulation (inside rep window only) ───────────────
            self._accumulate_violations(rule, vnames)

            # ── Speed frame counter ──────────────────────────────────────────
            if self._started[rule.name]:
                self._rep_frame_counts[rule.name] += 1

            # ─────────────────────────────────────────────────────────────────
            # PATH A — Standard exercises (no ROM gate, or simple up/down only)
            # ─────────────────────────────────────────────────────────────────
            if not has_rom:
                # Optional top-extreme tracking even on the standard path
                rom_max = getattr(rule, "max_rom_angle", None)
                if rom_max is not None and angle >= rom_max:
                    state.reached_top = True

                if angle <= rule.down_angle:
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)

                elif angle >= rule.up_angle:
                    if self._started[rule.name] and state.stage == STAGE_DOWN:
                        if self._check_sync_group_ready(rule, angles):
                            too_fast = (
                                rule.min_rep_frames > 0
                                and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                            )
                            # ROM quality gate if configured on standard path
                            rom_min  = getattr(rule, "min_rom_angle", None)
                            rom_good = True
                            if rom_min is not None and not state.reached_bottom:
                                rom_good = False
                            if rom_max is not None and not getattr(state, "reached_top", False):
                                rom_good = False

                            good = (
                                rom_good
                                and not self._pending_violations[rule.name]
                                and not too_fast
                            )
                            if rule.sync_group:
                                self._sync_group_count(rule, good=good, too_fast=too_fast)
                            else:
                                self._count_rep(rule, state, good=good, too_fast=too_fast)
                    state.stage = STAGE_UP

            # ─────────────────────────────────────────────────────────────────
            # PATH B — ROM-managed exercises (max_rom_angle is set)
            #
            # State machine:
            #   UP  ──(angle <= down_angle)──►  DOWN
            #   DOWN ──(angle >= up_angle)───►  RETURNING
            #   RETURNING ──(angle >= rom_max AND stable AND reversing)──► UP (rep counted)
            #   RETURNING ──(angle <= down_angle = bail-out)──► DOWN (BAD rep)
            # ─────────────────────────────────────────────────────────────────
            else:
                rom_min = getattr(rule, "min_rom_angle", None)
                rom_max = rule.max_rom_angle

                # Track bottom depth
                if rom_min is not None and angle <= rom_min:
                    state.reached_bottom = True

                # Track frames at or above the top extreme (stability gate)
                if angle >= rom_max:
                    self._stability_counts[rule.name] += 1
                    state.reached_top = True
                else:
                    # Drop below max_rom → reset stability counter.
                    # (We intentionally reset here so the athlete must be
                    #  consistently above the threshold — not just touch-and-go.)
                    self._stability_counts[rule.name] = 0

                # ── DOWN phase begins (or RETURNING bail-out) ─────────────────
                if angle <= rule.down_angle:
                    if state.stage == STAGE_RETURNING:
                        # Bail: user reversed back down before fully extending.
                        if self._started[rule.name]:
                            self._count_rep(rule, state, good=False)
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)

                # ── Enter RETURNING when crossing up_angle from DOWN ───────────
                elif (
                    angle >= rule.up_angle
                    and state.stage == STAGE_DOWN
                    and self._started[rule.name]
                ):
                    state.stage = STAGE_RETURNING
                    self._peak_angles[rule.name] = angle

                # Update peak angle while in RETURNING stage to support hysteresis
                if state.stage == STAGE_RETURNING:
                    self._peak_angles[rule.name] = max(self._peak_angles[rule.name], angle)

                # ── Rep completion: top extreme reached + stable + reversing ───
                if state.stage == STAGE_RETURNING and angle >= rom_max:
                    # Stability gate: require N consecutive frames at/above
                    # max_rom_angle before allowing reversal count.  N comes from
                    # rule.stability_frames if set (>= 0), otherwise the global
                    # _STABILITY_FRAMES_REQUIRED.  Set to 1 for fast exercises
                    # (lateral raise) where the user reverses immediately.
                    _sf = getattr(rule, "stability_frames", -1)
                    required = _sf if _sf >= 0 else _STABILITY_FRAMES_REQUIRED
                    stability_ok = (
                        required == 0 or self._stability_counts[rule.name] >= required
                    )

                    # Check for reversal with hysteresis
                    hysteresis = getattr(rule, "reversal_hysteresis", 0.0)
                    is_reversing = False
                    if hysteresis > 0.0:
                        is_reversing = angle < (self._peak_angles[rule.name] - hysteresis)
                    else:
                        is_reversing = angle < prev_angle

                    if is_reversing and stability_ok:
                        # Collect any last-frame violations before finalising.
                        # Exclude the ROM validation rule (same name as counter
                        # rule) — it fires "FAILED" during RETURNING by design
                        # and must not mark the rep BAD.
                        current_viols: Set[str] = {
                            v for v in vnames
                            if v.startswith(rule.name) and v != rule.name
                        }
                        if rule is self.counter.rules[0]:
                            counter_rule_names = {r.name for r in self.counter.rules}
                            current_viols.update(
                                v for v in vnames
                                if not any(v.startswith(cr) for cr in counter_rule_names)
                            )
                        has_violation = (
                            self._pending_violations[rule.name] or bool(current_viols)
                        )

                        if self._check_sync_group_ready(rule, angles):
                            too_fast = (
                                rule.min_rep_frames > 0
                                and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                            )
                            good = (
                                state.reached_bottom
                                and not has_violation
                                and not too_fast
                            )
                            if rule.sync_group:
                                self._sync_group_count(rule, good=good, too_fast=too_fast)
                            else:
                                self._count_rep(rule, state, good=good, too_fast=too_fast)
                            state.stage = STAGE_UP

        return self.counter.states
