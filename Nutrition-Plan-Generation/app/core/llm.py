"""
GoogleGenAIChat — LangChain BaseChatModel wrapper for Google GenAI / Gemini API.
The API key and model name are loaded from settings (GEMINI_API_KEY / GEMINI_MODEL in .env).

Retry strategy
--------------
Retries automatically with exponential back-off on rate limits or transient errors.
"""

import asyncio
import json
import os
import random
import re
import time
from typing import Any, List, Optional

from google import genai
from google.genai import types
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES: int = 8
BASE_BACKOFF_S: float = 1.5
MAX_BACKOFF_S: float = 30.0
JITTER_S: float = 0.5


def _backoff(attempt: int) -> float:
    """Exponential back-off with jitter. attempt is 0-indexed."""
    wait = min(BASE_BACKOFF_S * (2**attempt), MAX_BACKOFF_S)
    wait += random.uniform(0, JITTER_S)
    return wait


def _is_rate_limit_error(exc: Exception) -> bool:
    """Check if an exception is caused by Gemini/Google GenAI rate limiting (HTTP 429 / RESOURCE_EXHAUSTED)."""
    exc_str = str(exc).lower()
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429:
        return True
    indicators = [
        "429",
        "resource_exhausted",
        "resource has been exhausted",
        "quota exceeded",
        "rate limit",
        "too many requests",
        "rate_limit_exceeded",
        "exceeded your current quota",
    ]
    return any(ind in exc_str for ind in indicators)


def _get_retry_wait_time(attempt: int, exc: Optional[Exception]) -> float:
    """Determine wait duration: 62s for 15 RPM quota limit window reset, exponential backoff for others."""
    if exc and _is_rate_limit_error(exc):
        # 60s + 2-4s jitter to ensure 15 requests/minute quota bucket completely clears
        return 62.0 + random.uniform(0.5, 3.0)
    return _backoff(attempt)


def _clean_and_parse_json(text: str) -> Any:
    """Extract and parse JSON from an LLM response string."""
    text = text.strip()

    # 1. Strip markdown code fence if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
    else:
        # 2. Look for outermost { ... } or [ ... ]
        start_brace = text.find("{")
        start_bracket = text.find("[")
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            end_brace = text.rfind("}")
            candidate = text[start_brace : end_brace + 1] if end_brace != -1 else text
        elif start_bracket != -1:
            end_bracket = text.rfind("]")
            candidate = text[start_bracket : end_bracket + 1] if end_bracket != -1 else text
        else:
            candidate = text

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse LLM output as JSON: {text}") from exc


class GoogleGenAIChat(BaseChatModel):
    """LangChain-compatible chat model that calls Google GenAI / Gemini."""

    model_id: Optional[str] = None
    temperature: float = 0.7
    max_retries: int = MAX_RETRIES
    timeout: int = 3600

    @property
    def model_name(self) -> str:
        return (
            self.model_id
            or os.getenv("GEMINI_MODEL")
            or os.getenv("MODEL_NAME")
            or settings.gemini_model
            or settings.model_name
            or "gemini-3.5-flash-lite"
        )

    @property
    def _llm_type(self) -> str:
        return "google_genai_chat"

    def _get_client(self) -> genai.Client:
        api_key = (
            settings.gemini_api_key
            or settings.google_api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not set. Please add it to your .env file.")
        return genai.Client(api_key=api_key)

    def _format_contents(self, messages: List[BaseMessage]) -> tuple[str, list[types.Content]]:
        system_instruction = "You are a helpful nutrition and diet assistant."
        contents: list[types.Content] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_instruction = msg.content if isinstance(msg.content, str) else str(msg.content)
            elif isinstance(msg, HumanMessage):
                if isinstance(msg.content, str):
                    text = msg.content
                elif isinstance(msg.content, list):
                    text = " ".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in msg.content
                    )
                else:
                    text = str(msg.content)
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=text)]))
            elif isinstance(msg, AIMessage):
                content_str = msg.content if isinstance(msg.content, str) else str(msg.content)
                contents.append(types.Content(role="model", parts=[types.Part.from_text(text=content_str)]))

        if not contents:
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text="Hello")]))

        return system_instruction, contents

    def _build_payload(self, messages: List[BaseMessage], **kwargs: Any) -> tuple[dict, dict]:
        system_instruction, contents = self._format_contents(messages)
        payload_messages = []
        for c in contents:
            role = "user" if c.role == "user" else "assistant"
            part_text = " ".join(p.text for p in c.parts if getattr(p, "text", None))
            payload_messages.append({"role": role, "content": part_text})
        return {"messages": payload_messages, "system_prompt": system_instruction, "model_id": self.model_name}, {}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        client = self._get_client()
        system_instruction, contents = self._format_contents(messages)
        temp = kwargs.get("temperature", self.temperature)

        generate_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temp,
            max_output_tokens=kwargs.get("max_tokens", 8192),
            stop_sequences=stop,
        )

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=generate_config,
                )
                ai_text = response.text or ""
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=ai_text))])
            except Exception as exc:
                last_exc = exc
                wait = _get_retry_wait_time(attempt, exc)
                if _is_rate_limit_error(exc):
                    logger.warning(
                        "Google GenAI 15 RPM rate limit reached. Waiting %.1fs for quota window to reset before retry %d/%d...",
                        wait, attempt + 2, self.max_retries,
                    )
                else:
                    logger.warning(
                        "Google GenAI attempt %d/%d failed: %s — retrying in %.1fs",
                        attempt + 1, self.max_retries, exc, wait,
                    )
                if attempt < self.max_retries - 1:
                    time.sleep(wait)

        logger.error("Google GenAI request failed after %d attempts: %s", self.max_retries, last_exc)
        raise last_exc or RuntimeError(f"Google GenAI request failed after {self.max_retries} attempts")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._generate(messages, stop=stop, run_manager=run_manager, **kwargs),
        )


# Alias for backward compatibility
ITIBedrockChat = GoogleGenAIChat


def get_llm(temperature: float = 0.7, model_id: Optional[str] = None) -> GoogleGenAIChat:
    """Build a fresh GoogleGenAIChat client using the centrally configured model in .env."""
    return GoogleGenAIChat(
        model_id=model_id or os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or settings.gemini_model,
        temperature=temperature,
    )
