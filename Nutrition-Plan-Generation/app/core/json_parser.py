"""
Robust JSON extractor for LLM outputs.

Handles text produced by models such as openai/gpt-oss-120b, llama-3.3-70b, or deepseek-r1,
which may include <think>...</think> reasoning blocks, conversational text, or various
markdown fence formats around the JSON payload.
"""

import re
import json
from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_json(raw_text: str) -> dict[str, Any]:
    """
    Extract and parse a JSON dictionary from raw LLM text.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Cannot extract JSON from empty response.")

    # 1. Strip <think>...</think> tags if present (from reasoning models like deepseek-r1 / gpt-oss)
    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

    # 2. Try to find markdown code fences with JSON
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Try finding the outermost JSON object braces {...}
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = cleaned[first_brace : last_brace + 1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as exc:
            logger.debug("Brace extraction failed: %s", exc)

    # 4. Fallback: try parsing the whole cleaned string directly
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"No valid JSON object found in LLM output. Snippet: {raw_text[:250]}..."
        ) from exc
