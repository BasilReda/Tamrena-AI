"""
This repo has no setup.py/pyproject.toml pytest config, so `from src...`
imports in test files don't resolve unless backend/ (this file's parent)
is on sys.path. pytest auto-loads conftest.py before collecting any test
in this directory or below, so this runs once for the whole tests/ tree —
individual test files don't need their own sys.path.insert (see
tests/integration/test_architecture.py for the old per-file workaround
this replaces going forward).
"""

import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("MODEL_PATH", "assets/models/pose_landmarker_lite.task")

# ── Stub mediapipe (only PoseService needs it; these tests never call it) ──
_mp = types.ModuleType("mediapipe")
_mp_tasks = types.ModuleType("mediapipe.tasks")
_mp_python = types.ModuleType("mediapipe.tasks.python")
_mp_python.vision = types.ModuleType("mediapipe.tasks.python.vision")
_mp.tasks = _mp_tasks
_mp_tasks.python = _mp_python
sys.modules.update({
    "mediapipe": _mp,
    "mediapipe.tasks": _mp_tasks,
    "mediapipe.tasks.python": _mp_python,
    "mediapipe.tasks.python.vision": _mp_python.vision,
})
