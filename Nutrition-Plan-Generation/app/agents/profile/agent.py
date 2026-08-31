"""
Profile Agent — LLM-powered node.

Transforms the raw GenerateNutritionRequest into a normalised
NutritionProfile by calling Google GenAI / Gemini via LangChain.
LangSmith tracing is enabled automatically through the LANGCHAIN_* env vars.
"""

import json

from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.profile.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.schemas.profile import NutritionProfile
from app.schemas.request import GenerateNutritionRequest
from app.core.config import settings
from app.core.logging import get_logger
from app.core.json_parser import extract_json
from app.core.llm import GoogleGenAIChat

logger = get_logger(__name__)


def _escape_delimiter_lookalikes(text: str) -> str:
    """Neutralizes literal '<'/'>' in untrusted text so it can't fake a
    </user_data> closing tag (or any other tag-like sequence) to break out
    of the delimited block it's placed inside."""
    return text.replace("<", "&lt;").replace(">", "&gt;")


# ─── Lazy LLM factory ────────────────────────────────────────────────────────
_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = GoogleGenAIChat(
            temperature=0.1,
        )
    return _llm


async def run_profile_agent(request: GenerateNutritionRequest) -> NutritionProfile:
    """
    Call the Profile Agent to normalise the user request.
    Returns a validated NutritionProfile.
    """
    user_msg = USER_PROMPT_TEMPLATE.format(
        age=request.age,
        gender=request.gender.value,
        height_cm=request.height_cm,
        weight_kg=request.weight_kg,
        goal=request.goal.value,
        activity_level=request.activity_level.value,
        diet_type=request.diet_type.value,
        preferences=_escape_delimiter_lookalikes(", ".join(request.preferences)) or "None",
        allergies=_escape_delimiter_lookalikes(", ".join(request.allergies)) or "None",
        notes=_escape_delimiter_lookalikes(request.additional_notes) if request.additional_notes else "None",
    )

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)]

    last_error = None
    for attempt in range(1, 4):
        try:
            active_model = _get_llm().model_name
            logger.info("Profile Agent → calling Gemini (%s, attempt=%d)", active_model, attempt)
            response = await _get_llm().ainvoke(messages)
            raw = response.content.strip()

            if not raw:
                meta = getattr(response, "response_metadata", {})
                finish_reason = meta.get("finish_reason", "unknown")
                logger.warning("Attempt %d produced empty content (finish_reason=%s)", attempt, finish_reason)
                raise ValueError(f"LLM returned empty content (finish_reason={finish_reason}).")

            data = extract_json(raw)
            profile = NutritionProfile(**data)
            logger.info(
                "Profile Agent completed | goal=%s  activity=%s",
                profile.goal,
                profile.activity_level,
            )
            return profile
        except Exception as exc:
            last_error = exc
            logger.warning("Profile Agent attempt %d failed: %s", attempt, exc)
            if attempt < 3:
                messages.append(HumanMessage(content="Your previous output was empty or invalid JSON. Please provide ONLY the complete, valid JSON object matching the schema without truncation."))

    raise ValueError(f"Profile Agent failed after 3 attempts: {last_error}") from last_error
