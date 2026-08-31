"""
Central configuration for the Tamreena Web BFF — environment loading.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# ── DynamoDB (this service's OWN table, never Tamreena_AI's) ──────────
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "workout_users")
LIVE_SESSIONS_TABLE_NAME = os.getenv("LIVE_SESSIONS_TABLE_NAME", "workout_live_sessions")
# Owner lookup for Computer-Vision resources (upload ids, cv session ids).
# Computer-Vision itself has no user model or auth (see CV_API_URL below) —
# this table is what lets the BFF stop one signed-in user from reading
# another user's uploaded video or session report by id.
LIVE_SESSION_OWNERSHIP_TABLE_NAME = os.getenv("LIVE_SESSION_OWNERSHIP_TABLE_NAME", "live_session_ownership")

# ── Auth ──────────────────────────────────────────────────────────────
# JWT_SECRET MUST match Tamreena_AI's own JWT_SECRET exactly — tokens
# minted here are verified by that repo's API using this same secret.
# See Tamreena_AI/docs/superpowers/specs/2026-07-25-bff-auth-handoff-design.md.
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days, matches Tamreena_AI's own token lifetime

# ── Tamreena_AI proxy ────────────────────────────────────────────────
# Base URL for Tamreena_AI's plan-generation API. Every workout proxy route
# forwards the caller's own Bearer token here — see docs/superpowers/specs/
# 2026-07-25-website-shell-home-workout-design.md in Tamreena_AI.
WORKOUT_API_URL = os.getenv("WORKOUT_API_URL", "http://localhost:8001")

# ── Computer-Vision proxy ────────────────────────────────────────────────
# Base URL for the Computer-Vision service's exercise catalogue API. That
# service has no auth of its own — see app/tamreena_client.py's
# call_upstream() for how calls to it omit the Authorization header.
CV_API_URL = os.getenv("CV_API_URL", "http://localhost:8002")

# ── Nutrition-Plan-Generation proxy ──────────────────────────────────
# Base URL for the AWS-hosted Nutrition-Plan-Generation service API.
# Endpoint: http://nutrition-agent.fitness-app-prod.local:8000/generate-plan
NUTRITION_AGENT_URL = os.getenv("NUTRITION_AGENT_URL", os.getenv("NUTRITION_API_URL", "http://nutrition-agent.fitness-app-prod.local:8000"))
NUTRITION_API_URL = NUTRITION_AGENT_URL

# ── Internal service auth ────────────────────────────────────────────
# Shared secret proving a request to Computer-Vision or Nutrition-Plan-
# Generation actually came from this BFF. Both of those services have no
# user-level auth of their own (see CV_API_URL/NUTRITION_API_URL above)
# and independently enforce this same value via their own
# X-Internal-Auth check — this value MUST match what's configured there.
INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN", "")

