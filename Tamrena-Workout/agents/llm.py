"""
Shared LLM client factory.

All agents (supervisor, exercise-recommender, plan-assembler, coach) and
the InBody/RAG pipelines use the Google GenAI / Gemini client configured via .env.
"""

import asyncio
import base64
import json
import os
import random
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence, Union

from google import genai
from google.genai import types
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import BaseModel

import config

# Retry configuration for rate limiting / transient API issues
_MAX_RETRIES: int = 8
_BASE_BACKOFF_S: float = 1.5
_MAX_BACKOFF_S: float = 30.0
_JITTER_S: float = 0.5


def _backoff(attempt: int) -> float:
    wait = min(_BASE_BACKOFF_S * (2**attempt), _MAX_BACKOFF_S)
    return wait + random.uniform(0, _JITTER_S)


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

    # Try direct parse
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 3. Clean common issues: trailing commas before } or ]
    fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse LLM output as JSON: {text}") from exc


def _parse_tool_calls(ai_text: str) -> Optional[List[Dict[str, Any]]]:
    """Detects the `{"tool_calls": [...]}` envelope the model is instructed to
    emit and converts it into LangChain's ToolCall dict shape."""
    try:
        data = _clean_and_parse_json(ai_text)
    except ValueError:
        return None

    if not isinstance(data, dict) or not isinstance(data.get("tool_calls"), list):
        return None

    calls: List[Dict[str, Any]] = []
    for tc in data["tool_calls"]:
        if isinstance(tc, dict) and isinstance(tc.get("name"), str):
            args = tc.get("arguments", tc.get("args", {}))
            calls.append(
                {
                    "name": tc["name"],
                    "args": args if isinstance(args, dict) else {},
                    "id": f"call_{uuid.uuid4().hex[:16]}",
                    "type": "tool_call",
                }
            )
    return calls or None


def _openai_tools_to_gemini(tools: List[Dict[str, Any]]) -> list:
    """Convert the OpenAI-style tool schemas LangChain hands us
    (``{"type": "function", "function": {name, description, parameters}}``)
    into a single Gemini ``Tool`` with one ``FunctionDeclaration`` per tool.

    google-genai >= 2.x accepts a full JSON Schema via ``parameters_json_schema``
    (no need to down-convert to the OpenAPI subset).
    """
    declarations = []
    for t in tools or []:
        fn = t.get("function", t) if isinstance(t, dict) else {}
        name = fn.get("name")
        if not name:
            continue
        params = fn.get("parameters") or {"type": "object", "properties": {}}
        declarations.append(
            types.FunctionDeclaration(
                name=name,
                description=fn.get("description") or "",
                parameters_json_schema=params,
            )
        )
    return [types.Tool(function_declarations=declarations)] if declarations else []


def _validate_schema(data: Any, schema: Any) -> Any:
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        if hasattr(schema, "model_validate"):
            return schema.model_validate(data)
        elif hasattr(schema, "parse_obj"):
            return schema.parse_obj(data)
        return schema(**data)
    return data


def _get_schema_instructions(schema: Any) -> str:
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        if hasattr(schema, "model_json_schema"):
            schema_dict = schema.model_json_schema()
        elif hasattr(schema, "schema"):
            schema_dict = schema.schema()
        else:
            schema_dict = {}
        schema_json = json.dumps(schema_dict, indent=2)
    elif isinstance(schema, dict):
        schema_json = json.dumps(schema, indent=2)
    else:
        schema_json = str(schema)

    return (
        f"\n\nYou MUST respond with ONLY a valid JSON object conforming strictly to this JSON Schema:\n"
        f"```json\n{schema_json}\n```\n"
        f"Output ONLY the raw JSON object and nothing else. Do not include any markdown fences or explanations outside the JSON."
    )


def _inject_instructions(input_val: Any, instructions: str) -> list[BaseMessage]:
    if isinstance(input_val, PromptValue):
        msgs = input_val.to_messages()
    elif isinstance(input_val, list):
        msgs = list(input_val)
    elif isinstance(input_val, str):
        return [HumanMessage(content=input_val + instructions)]
    elif isinstance(input_val, BaseMessage):
        msgs = [input_val]
    else:
        return [HumanMessage(content=str(input_val) + instructions)]

    out_msgs: list[BaseMessage] = []
    for m in msgs:
        if isinstance(m, HumanMessage):
            if isinstance(m.content, str):
                out_msgs.append(HumanMessage(content=m.content))
            elif isinstance(m.content, list):
                out_msgs.append(HumanMessage(content=m.content))
            else:
                out_msgs.append(m)
        else:
            out_msgs.append(m)

    if out_msgs and isinstance(out_msgs[-1], HumanMessage) and isinstance(out_msgs[-1].content, str):
        out_msgs[-1] = HumanMessage(content=out_msgs[-1].content + instructions)
    else:
        out_msgs.append(HumanMessage(content=instructions.strip()))

    return out_msgs


class _GoogleStructuredOutputRunnable(Runnable):
    """Wraps GoogleGenAIChat to provide structured output via prompt formatting and JSON parsing."""

    def __init__(self, llm: "GoogleGenAIChat", schema: Any, include_raw: bool = False, **kwargs: Any):
        self.llm = llm
        self.schema = schema
        self.include_raw = include_raw
        self.kwargs = kwargs
        self.instructions = _get_schema_instructions(schema)

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        messages = _inject_instructions(input, self.instructions)
        res = self.llm.invoke(messages, config=config, **self.kwargs)
        raw_text = res.content if isinstance(res, BaseMessage) else str(res)
        try:
            parsed_data = _clean_and_parse_json(raw_text)
            validated = _validate_schema(parsed_data, self.schema)
            if self.include_raw:
                return {"raw": res, "parsed": validated, "parsing_error": None}
            return validated
        except Exception as exc:
            if self.include_raw:
                return {"raw": res, "parsed": None, "parsing_error": exc}
            raise

    async def ainvoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        messages = _inject_instructions(input, self.instructions)
        res = await self.llm.ainvoke(messages, config=config, **self.kwargs)
        raw_text = res.content if isinstance(res, BaseMessage) else str(res)
        try:
            parsed_data = _clean_and_parse_json(raw_text)
            validated = _validate_schema(parsed_data, self.schema)
            if self.include_raw:
                return {"raw": res, "parsed": validated, "parsing_error": None}
            return validated
        except Exception as exc:
            if self.include_raw:
                return {"raw": res, "parsed": None, "parsing_error": exc}
            raise


class GoogleGenAIChat(BaseChatModel):
    """LangChain-compatible chat model that calls Google GenAI / Gemini."""

    model_name: str = "gemini-3.5-flash-lite"
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_retries: int = _MAX_RETRIES
    timeout: int = 3600

    @property
    def model_id(self) -> str:
        return self.model_name

    @property
    def _llm_type(self) -> str:
        return "google_genai_chat"

    def _get_client(self) -> genai.Client:
        key = self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or config.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not set. Please add it to your .env file.")
        return genai.Client(api_key=key)

    def _use_native_fc(self, tools: Any) -> bool:
        """Gemini models do native function calling; the text-envelope hack is
        only for models without it (e.g. Gemma). A Gemini model asked to emit
        the ``{"tool_calls": [...]}`` text instead reliably returns
        finish_reason=MALFORMED_FUNCTION_CALL with an empty body, which
        silently ends the agent graph."""
        return bool(tools) and "gemini" in (self.model_name or "").lower()

    def _format_contents(self, messages: List[BaseMessage], **kwargs: Any) -> tuple[str, list[types.Content]]:
        system_instruction = "You are a helpful fitness and workout assistant."
        contents: list[types.Content] = []

        tools = kwargs.get("tools")
        native_fc = self._use_native_fc(tools)
        tool_instructions = ""
        if tools and not native_fc:
            tool_instructions = (
                "\n\nYou have access to the following tools:\n"
                f"```json\n{json.dumps(tools, indent=2)}\n```\n"
                "To call a tool, respond with ONLY this JSON and nothing else "
                '(no markdown fences, no extra text): '
                '{"tool_calls": [{"name": "<tool_name>", "arguments": {<args as an object>}}]}\n'
                "To give a final answer instead of calling a tool, respond with plain text, "
                "not JSON.\n\n"
                "IMPORTANT: once you start a multi-step task, do not stop to explain your "
                "reasoning in plain text between steps — after a tool result comes back, "
                "immediately continue with the next required tool call in the exact JSON "
                "format above. Only respond with plain text when the ENTIRE task is fully "
                "complete and no further tool calls are needed."
            )

        for msg in messages:
            if isinstance(msg, SystemMessage):
                content_str = msg.content if isinstance(msg.content, str) else str(msg.content)
                system_instruction = content_str
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
                if msg.tool_calls and native_fc:
                    parts = []
                    if isinstance(msg.content, str) and msg.content.strip():
                        parts.append(types.Part.from_text(text=msg.content))
                    sigs = (msg.additional_kwargs or {}).get("__gemini_thought_signatures", {})
                    for tc in msg.tool_calls:
                        fc_part = types.Part.from_function_call(name=tc["name"], args=tc.get("args", {}) or {})
                        # Gemini 3 rejects function_call history that omits the
                        # thought_signature it originally returned.
                        b64 = sigs.get(tc.get("id"))
                        if b64:
                            try:
                                fc_part.thought_signature = base64.b64decode(b64)
                            except Exception:
                                pass
                        parts.append(fc_part)
                    contents.append(types.Content(role="model", parts=parts))
                else:
                    if msg.tool_calls:
                        content_str = json.dumps(
                            {
                                "tool_calls": [
                                    {"name": tc["name"], "arguments": tc.get("args", {})}
                                    for tc in msg.tool_calls
                                ]
                            }
                        )
                    else:
                        content_str = msg.content if isinstance(msg.content, str) else str(msg.content)
                    contents.append(types.Content(role="model", parts=[types.Part.from_text(text=content_str)]))
            elif isinstance(msg, ToolMessage):
                result_text = msg.content if isinstance(msg.content, str) else str(msg.content)
                if native_fc:
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_function_response(
                                    name=msg.name or "tool",
                                    response={"result": result_text},
                                )
                            ],
                        )
                    )
                else:
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=f"[Result of tool '{msg.name}']: {result_text}")],
                        )
                    )

        if tool_instructions:
            system_instruction += tool_instructions
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=(
                                "Reminder: if this task isn't fully complete yet, respond with ONLY "
                                'the {"tool_calls": [...]} JSON now — do not explain your reasoning '
                                "first. Plain text is only for a fully finished task."
                            )
                        )
                    ],
                )
            )

        if not contents:
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text="Hello")]))

        return system_instruction, contents

    def _build_payload(self, messages: List[BaseMessage], **kwargs: Any) -> tuple[dict, dict]:
        """Convert messages to payload dictionary for inspection / compatibility."""
        system_instruction, contents = self._format_contents(messages, **kwargs)
        payload_messages = []
        for c in contents:
            role = "user" if c.role == "user" else "assistant"
            part_text = " ".join(p.text for p in c.parts if getattr(p, "text", None))
            payload_messages.append({"role": role, "content": part_text})
        return {"messages": payload_messages, "system_prompt": system_instruction, "model_id": self.model_name}, {}

    @staticmethod
    def _to_ai_message(ai_text: str, tools_bound: bool) -> AIMessage:
        tool_calls = _parse_tool_calls(ai_text) if tools_bound else None
        if tool_calls:
            return AIMessage(content="", tool_calls=tool_calls)
        return AIMessage(content=ai_text)

    @staticmethod
    def _response_text(response: Any) -> str:
        """Concatenate only the text parts of a Gemini response.

        ``response.text`` raises/warns and returns nothing useful when the
        candidate also contains non-text parts (e.g. a native ``function_call``)
        — read the parts directly so a mixed response still yields its text.
        """
        try:
            parts = response.candidates[0].content.parts or []
            text = "".join(getattr(p, "text", "") or "" for p in parts)
            if text:
                return text
        except (AttributeError, IndexError, TypeError):
            pass
        try:
            return response.text or ""
        except Exception:
            return ""

    @staticmethod
    def _extract_native_tool_calls(response: Any) -> Optional[List[Dict[str, Any]]]:
        """Newer Gemini models (e.g. gemini-2.x / 3.x flash) emit real
        ``function_call`` parts instead of the prompt-injected
        ``{"tool_calls": [...]}`` text envelope this client asks for. Those
        parts are invisible to ``response.text``, so without this the agent's
        tool call is silently dropped and the orchestration graph ends early
        (no sub-agents dispatched, empty plan). Convert them to LangChain
        tool-call dicts so both calling styles work.
        """
        try:
            parts = response.candidates[0].content.parts or []
        except (AttributeError, IndexError, TypeError):
            return None

        calls: List[Dict[str, Any]] = []
        signatures: Dict[str, str] = {}
        for part in parts:
            fc = getattr(part, "function_call", None)
            if not fc or not getattr(fc, "name", None):
                continue
            raw_args = getattr(fc, "args", None) or {}
            try:
                args = json.loads(json.dumps(dict(raw_args), default=str))
            except (TypeError, ValueError):
                args = dict(raw_args) if hasattr(raw_args, "keys") else {}
            call_id = f"call_{uuid.uuid4().hex[:16]}"
            calls.append(
                {
                    "name": fc.name,
                    "args": args if isinstance(args, dict) else {},
                    "id": call_id,
                    "type": "tool_call",
                }
            )
            sig = getattr(part, "thought_signature", None)
            if sig:
                signatures[call_id] = base64.b64encode(sig).decode("ascii") if isinstance(sig, (bytes, bytearray)) else str(sig)
        if not calls:
            return None
        return calls, signatures

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        client = self._get_client()
        system_instruction, contents = self._format_contents(messages, **kwargs)
        raw_tools = kwargs.get("tools")
        tools_bound = bool(raw_tools)
        native_fc = self._use_native_fc(raw_tools)
        temp = kwargs.get("temperature", self.temperature)
        if tools_bound:
            temp = min(temp, 0.15)

        config_kwargs: Dict[str, Any] = dict(
            system_instruction=system_instruction,
            temperature=temp,
            max_output_tokens=kwargs.get("max_tokens", 8192),
            stop_sequences=stop,
        )
        if native_fc:
            config_kwargs["tools"] = _openai_tools_to_gemini(raw_tools)
            # We drive the tool loop through LangGraph, so the SDK must not try
            # to execute functions itself.
            config_kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
        generate_config = types.GenerateContentConfig(**config_kwargs)

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=generate_config,
                )
                native = self._extract_native_tool_calls(response) if tools_bound else None
                if native:
                    native_calls, signatures = native
                    extra = {"__gemini_thought_signatures": signatures} if signatures else {}
                    message = AIMessage(content="", tool_calls=native_calls, additional_kwargs=extra)
                else:
                    message = self._to_ai_message(self._response_text(response), tools_bound)

                # A Gemini response that produced neither text nor a usable
                # function call (finish_reason MALFORMED_FUNCTION_CALL, or an
                # empty candidate) would end the agent graph as if the model
                # gave a final answer. Retry instead — it almost always
                # succeeds on the next attempt.
                if tools_bound and not message.content and not getattr(message, "tool_calls", None):
                    finish_reason = None
                    try:
                        finish_reason = str(response.candidates[0].finish_reason)
                    except (AttributeError, IndexError, TypeError):
                        pass
                    if os.getenv("LLM_DEBUG"):
                        print(f"[LLM_DEBUG] empty tool-turn (finish_reason={finish_reason}) — attempt {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        time.sleep(_backoff(attempt))
                        continue
                return ChatResult(generations=[ChatGeneration(message=message)])
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries - 1:
                    wait_seconds = _get_retry_wait_time(attempt, exc)
                    if _is_rate_limit_error(exc):
                        print(
                            f"[GoogleGenAIChat] Gemini rate limit reached (15 RPM quota). "
                            f"Waiting {wait_seconds:.1f}s for quota bucket reset before retry {attempt + 2}/{self.max_retries}..."
                        )
                    time.sleep(wait_seconds)

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

    def with_structured_output(
        self,
        schema: Any,
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Runnable:
        """Returns a Runnable that prompts for structured JSON and validates the response."""
        return _GoogleStructuredOutputRunnable(self, schema, include_raw=include_raw, **kwargs)

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], type, "BaseTool", Any]],
        *,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> Runnable:
        """Prompt-injects tool schemas and parses response tool calls for ReAct compatibility."""
        formatted_tools = [convert_to_openai_tool(t) for t in tools]
        return self.bind(tools=formatted_tools, **kwargs)


# Alias for backward compatibility across existing references/tests
ITIBedrockChat = GoogleGenAIChat


def get_llm(temperature: float = 0.3) -> GoogleGenAIChat:
    """Build a fresh GoogleGenAIChat client using the centrally configured model in .env."""
    model_name = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or config.GEMINI_MODEL or "gemini-3.5-flash-lite"
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or config.GEMINI_API_KEY
    return GoogleGenAIChat(model_name=model_name, api_key=api_key, temperature=temperature)


def get_coach_llm(temperature: float = 0.4) -> GoogleGenAIChat:
    """Build the Coach Agent's LLM client using the centrally configured model in .env."""
    model_name = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or config.GEMINI_MODEL or "gemini-3.5-flash-lite"
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or config.GEMINI_API_KEY
    return GoogleGenAIChat(model_name=model_name, api_key=api_key, temperature=temperature)
