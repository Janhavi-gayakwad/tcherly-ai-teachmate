"""The TeachMate conversation loop on top of Gemini function calling.

`stream_reply` yields events for the UI:
  {"type": "status", "text": ...}        what the assistant is doing (tool calls)
  {"type": "delta", "text": ...}         a chunk of answer text
  {"type": "reset"}                      discard streamed text (switching to a fallback model)
  {"type": "proposal", "proposal": ...}  the assistant suggests saving a reflection
  {"type": "replace", "text": ...}       answer rewritten after a failed grounding check
  {"type": "final", "turn": AssistantTurn}
"""
import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai
from google.genai import errors, types

from . import grounding
from .config import settings
from .tools import ToolContext, gemini_tools

log = logging.getLogger("teachmate")

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text(encoding="utf-8")
CITATION = re.compile(r"\[(E\d+(?:\s*,\s*E\d+)*)\]")
# Overloaded (503/500/504) or rate-limited (429): worth trying the next model.
RETRYABLE_CODES = {429, 500, 503, 504}

TOOL_STATUS = {
    "get_lesson_overview": "Reading the whole-lecture overview",
    "get_segment_analytics": "Looking closely at min {start_min}-{end_min}",
    "find_moments": "Finding the key moments",
    "compare_course_lessons": "Comparing the lessons in this course",
    "get_teacher_reflections": "Checking your saved bookmarks and reflections",
    "propose_reflection": "Drafting a reflection for you to save",
}


@dataclass
class AssistantTurn:
    text: str
    model: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    cited: list[str] = field(default_factory=list)
    history: list[types.Content] = field(default_factory=list)
    grounding: dict[str, Any] = field(default_factory=dict)
    repaired: bool = False
    proposals: list[dict[str, Any]] = field(default_factory=list)


class ModelUnavailable(Exception):
    pass


def extract_citations(text: str) -> list[str]:
    ids: list[str] = []
    for group in CITATION.findall(text):
        for evidence_id in re.split(r"\s*,\s*", group):
            if evidence_id not in ids:
                ids.append(evidence_id)
    return ids


def _answer_text(content: types.Content) -> str:
    return "".join(p.text for p in content.parts or [] if p.text and not p.thought).strip()


class TeachMate:
    def __init__(self, api_key: str | None = None, models: list[str] | None = None):
        key = api_key or settings.gemini_api_key
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Create a free key at https://aistudio.google.com/apikey, "
                "put GEMINI_API_KEY=<your key> in the project's .env file, then restart TeachMate."
            )
        self.client = genai.Client(api_key=key)
        self.models = models or settings.gemini_models

    def _config(self, allow_tools: bool = True) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=gemini_tools(),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO" if allow_tools else "NONE")
            ),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def reply(self, ctx: ToolContext, message: str, history: list[types.Content] | None = None, page_context: str | None = None) -> AssistantTurn:
        """Non-streaming convenience wrapper (CLI, evaluation)."""
        async for event in self.stream_reply(ctx, message, history, page_context):
            if event["type"] == "final":
                return event["turn"]
        raise RuntimeError("no answer produced")

    async def stream_reply(
        self,
        ctx: ToolContext,
        message: str,
        history: list[types.Content] | None = None,
        page_context: str | None = None,
        repair: bool = True,
    ) -> AsyncIterator[dict[str, Any]]:
        user_parts = []
        if page_context:
            user_parts.append(types.Part.from_text(text=f"[Dashboard context: {page_context}]"))
        user_parts.append(types.Part.from_text(text=message))
        base = list(history or []) + [types.Content(role="user", parts=user_parts)]

        last_error: Exception | None = None
        for model in self.models:
            emitted = False
            proposals_start, evidence_start = len(ctx.proposals), len(ctx.evidence.items)
            ctx.begin_turn()
            try:
                async for event in self._run(model, ctx, list(base), repair):
                    if event["type"] in ("delta", "proposal"):
                        emitted = True
                    yield event
                return
            except ModelUnavailable as error:
                log.warning("model %s unavailable (%s); trying next model", model, error)
                last_error = error
                # The next model starts the turn afresh: drop this attempt's proposals and evidence.
                del ctx.proposals[proposals_start:]
                del ctx.evidence.items[evidence_start:]
                if emitted:
                    yield {"type": "reset"}
        raise RuntimeError(f"All Gemini models are busy or rate-limited right now ({last_error}). Please try again in a minute.")

    async def draft_reflection(self, history: list[types.Content], lesson_minutes: int) -> dict[str, Any]:
        """Summarise the conversation into an editable reflection (bookmark + question + action)."""
        schema = {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Short name for the lecture segment/concept (max 60 chars)"},
                "start_min": {"type": "integer"},
                "end_min": {"type": "integer"},
                "states": {"type": "array", "items": {"type": "string", "enum": ["difficult", "easy", "boring", "engaging"]}},
                "question": {"type": "string", "description": "The teacher's key reflective question or finding, first person"},
                "action": {"type": "string", "description": "An action the teacher said they took or will try; empty if none"},
            },
            "required": ["topic", "start_min", "end_min", "states", "question", "action"],
        }
        instruction = (
            "Summarise this conversation as a reflection the teacher can save in Tcherly. Use the teacher's own "
            "conclusions where they gave any; otherwise phrase the most important open question. Only include an "
            "action if the teacher expressed one or explicitly chose an option. Use the most specific time window the "
            f"conversation focused on (within 0-{lesson_minutes} min), not the whole lecture unless nothing narrower was "
            "discussed. Return JSON only."
        )
        contents = list(history) + [types.Content(role="user", parts=[types.Part.from_text(text=instruction)])]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_json_schema=schema,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        last_error: Exception | None = None
        for model in self.models:
            try:
                response = await asyncio.wait_for(
                    self.client.aio.models.generate_content(model=model, contents=contents, config=config),
                    timeout=settings.model_timeout_s,
                )
                draft = json.loads(response.text)
                draft["start_min"] = max(0, min(int(draft["start_min"]), lesson_minutes - 1))
                draft["end_min"] = max(draft["start_min"] + 1, min(int(draft["end_min"]), lesson_minutes))
                return draft
            except errors.APIError as error:
                if error.code not in RETRYABLE_CODES:
                    raise
                last_error = error
            except TimeoutError as error:
                last_error = error
        raise RuntimeError(f"Couldn't draft a reflection right now ({last_error}).")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _stream_round(self, model: str, contents: list[types.Content], allow_tools: bool) -> AsyncIterator[types.Part]:
        """Stream one model call, yielding parts. Raises ModelUnavailable on overload, rate limit or timeout."""
        try:
            stream = await asyncio.wait_for(
                self.client.aio.models.generate_content_stream(model=model, contents=contents, config=self._config(allow_tools)),
                timeout=settings.model_timeout_s,
            )
            iterator = stream.__aiter__()
            while True:
                try:
                    chunk = await asyncio.wait_for(iterator.__anext__(), timeout=settings.model_timeout_s)
                except StopAsyncIteration:
                    return
                candidate = chunk.candidates[0] if chunk.candidates else None
                if candidate and candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        yield part
        except errors.APIError as error:
            if error.code in RETRYABLE_CODES:
                raise ModelUnavailable(f"HTTP {error.code}") from error
            raise
        except TimeoutError as error:
            raise ModelUnavailable(f"timed out after {settings.model_timeout_s}s") from error

    async def _run(self, model: str, ctx: ToolContext, contents: list[types.Content], repair: bool) -> AsyncIterator[dict[str, Any]]:
        tool_calls: list[dict[str, Any]] = []
        turn_start = len(ctx.proposals)
        emitted_proposals: dict[str, str] = {}

        for round_no in range(settings.max_tool_rounds + 1):
            allow_tools = round_no < settings.max_tool_rounds
            parts: list[types.Part] = []
            async for part in self._stream_round(model, contents, allow_tools):
                parts.append(part)
                if part.text and not part.thought:
                    yield {"type": "delta", "text": part.text}
            if not parts:
                raise ModelUnavailable("empty response")

            # Keep every part as-is: they carry thought signatures Gemini needs on the next call.
            answer = types.Content(role="model", parts=parts)
            contents.append(answer)
            calls = [p.function_call for p in parts if p.function_call]
            if not calls:
                break

            for call in calls:
                args = dict(call.args or {})
                status = TOOL_STATUS.get(call.name, call.name)
                try:
                    status = status.format(**args)
                except (KeyError, IndexError):
                    status = status.split(" min ")[0]
                yield {"type": "status", "text": status}
            results = await asyncio.gather(*(ctx.run(call.name, dict(call.args or {})) for call in calls))
            for call, result in zip(calls, results):
                tool_calls.append({"name": call.name, "args": dict(call.args or {}), "error": result.get("error")})
            for proposal in ctx.proposals[turn_start:]:
                # Re-emit when a proposal was created or updated (same id = update the same card).
                fingerprint = json.dumps(proposal, sort_keys=True)
                if emitted_proposals.get(proposal["id"]) != fingerprint:
                    emitted_proposals[proposal["id"]] = fingerprint
                    yield {"type": "proposal", "proposal": proposal}
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(name=call.name, response=result) for call, result in zip(calls, results)],
                )
            )
        else:
            raise RuntimeError("tool loop ended without an answer")

        text = _answer_text(contents[-1])
        report = grounding.check(text, ctx.evidence)
        repaired = False

        if repair and not report.grounded:
            yield {"type": "status", "text": "Double-checking the numbers against the data"}
            fix = types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            "[Automatic grounding check] Some statements in your last answer don't match the evidence "
                            "you cited:\n" + report.feedback_for_model() + "\nRewrite the whole answer, correcting only "
                            "these problems (fix the number or the citation, or remove the claim). Keep everything else. "
                            "Reply with the corrected answer only."
                        )
                    )
                ],
            )
            repair_parts = [p async for p in self._stream_round(model, contents + [fix], allow_tools=False)]
            repaired_content = types.Content(role="model", parts=repair_parts)
            new_text = _answer_text(repaired_content)
            if new_text:
                new_report = grounding.check(new_text, ctx.evidence)
                if new_report.score >= report.score:
                    contents += [fix, repaired_content]
                    text, report, repaired = new_text, new_report, True
                    yield {"type": "replace", "text": text}

        yield {
            "type": "final",
            "turn": AssistantTurn(
                text=text,
                model=model,
                tool_calls=tool_calls,
                cited=extract_citations(text),
                history=contents,
                grounding=report.as_dict(),
                repaired=repaired,
                proposals=ctx.proposals[turn_start:],
            ),
        }
