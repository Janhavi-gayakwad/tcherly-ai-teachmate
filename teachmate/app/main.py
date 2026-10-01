"""TeachMate HTTP API.

Run from the repo root:
    teachmate/.venv/Scripts/python -m uvicorn app.main:app --app-dir teachmate --port 8000

The React dashboard sends the teacher's Tcherly access token in the
Authorization header. TeachMate verifies it (same JWT secret as Node) to know
which teacher is talking, and forwards it to the Node API for every data access,
where lesson ownership is enforced.
"""
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import store
from .assistant import AssistantTurn, TeachMate
from .auth import Teacher, current_teacher
from .config import settings
from .tcherly_client import TcherlyAPIError, TcherlyClient
from .tools import ToolContext

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("teachmate")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await store.ensure_indexes()
    yield


app = FastAPI(title="Tcherly TeachMate", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

assistant = TeachMate()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    lesson_id: str = Field(description="Lesson slug or _id")
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None
    range: tuple[int, int] | None = Field(default=None, description="Slider range selected on the dashboard, in minutes")


class ReflectionIn(BaseModel):
    lesson_id: str
    topic: str = Field(min_length=1, max_length=120)
    start_min: int = Field(ge=0)
    end_min: int = Field(ge=1)
    states: list[str] = Field(default_factory=list)
    question: str = Field(min_length=1, max_length=2000)
    action: str = Field(default="", max_length=2000)
    conversation_id: str | None = None
    proposal_id: str | None = None


class DraftRequest(BaseModel):
    conversation_id: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def open_lesson(teacher: Teacher, lesson_id: str, evidence=None) -> ToolContext:
    """Tool context for a lesson; fails with 401/403/404 if the teacher can't access it."""
    ctx = ToolContext(TcherlyClient(teacher.authorization), lesson_id, evidence)
    try:
        await ctx.lesson()
    except TcherlyAPIError as error:
        await ctx.client.aclose()
        raise HTTPException(status_code=error.status, detail=str(error))
    return ctx


async def load_conversation(teacher: Teacher, body: ChatRequest) -> tuple[dict, ToolContext]:
    doc = await store.get(body.conversation_id, teacher.id) if body.conversation_id else None
    evidence = store.evidence_from_doc(doc) if doc else None
    ctx = await open_lesson(teacher, body.lesson_id, evidence)
    lesson = await ctx.lesson()
    if doc is None or doc["lesson_id"] != str(lesson["_id"]):
        doc = await store.create(teacher.id, lesson)
        ctx.evidence = store.evidence_from_doc(doc)
    return doc, ctx


def page_context(body: ChatRequest) -> str | None:
    if not body.range:
        return None
    return f"the teacher currently has minutes {body.range[0]}-{body.range[1]} selected on the dashboard"


def assistant_message(turn: AssistantTurn, ctx: ToolContext) -> dict[str, Any]:
    return {
        "text": turn.text,
        "model": turn.model,
        "citations": {cid: e.fact for cid in turn.cited if (e := ctx.evidence.get(cid))},
        "tool_calls": turn.tool_calls,
        "grounding": turn.grounding,
        "repaired": turn.repaired,
        "proposals": turn.proposals,
    }


def sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "models": settings.gemini_models}


@app.post("/chat")
async def chat(body: ChatRequest, teacher: Teacher = Depends(current_teacher)) -> dict:
    """Non-streaming chat (used by the CLI and the evaluation script)."""
    doc, ctx = await load_conversation(teacher, body)
    try:
        turn = await assistant.reply(ctx, body.message, store.history_from_doc(doc), page_context(body))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))
    finally:
        await ctx.client.aclose()
    message = assistant_message(turn, ctx)
    await store.save_turn(doc, body.message, message, turn.history, ctx.evidence, turn.proposals)
    return {"conversation_id": doc["_id"], **message}


@app.post("/chat/stream")
async def chat_stream(body: ChatRequest, teacher: Teacher = Depends(current_teacher)) -> StreamingResponse:
    """Server-sent events: status / delta / reset / proposal / replace / done / error."""
    doc, ctx = await load_conversation(teacher, body)

    async def events():
        yield sse({"type": "start", "conversation_id": doc["_id"]})
        try:
            async for event in assistant.stream_reply(ctx, body.message, store.history_from_doc(doc), page_context(body)):
                if event["type"] == "final":
                    turn: AssistantTurn = event["turn"]
                    message = assistant_message(turn, ctx)
                    await store.save_turn(doc, body.message, message, turn.history, ctx.evidence, turn.proposals)
                    yield sse({"type": "done", "conversation_id": doc["_id"], "message": message})
                else:
                    yield sse(event)
        except Exception as error:  # surface any failure to the UI instead of silently closing the stream
            log.exception("chat stream failed")
            yield sse({"type": "error", "message": str(error) if isinstance(error, RuntimeError) else "Something went wrong. Please try again."})
        finally:
            await ctx.client.aclose()

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/conversations")
async def list_conversations(lesson_id: str = Query(...), teacher: Teacher = Depends(current_teacher)) -> list[dict]:
    ctx = await open_lesson(teacher, lesson_id)
    lesson = await ctx.lesson()
    await ctx.client.aclose()
    docs = await store.list_for_lesson(teacher.id, str(lesson["_id"]))
    return [{"id": d["_id"], "title": d.get("title") or "New conversation", "updated_at": d["updated_at"]} for d in docs if d.get("messages")]


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, teacher: Teacher = Depends(current_teacher)) -> dict:
    doc = await store.get(conversation_id, teacher.id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": doc["_id"],
        "lesson_id": doc["lesson_id"],
        "title": doc.get("title"),
        "messages": doc.get("messages", []),
        "proposals": doc.get("proposals", []),
    }


@app.post("/reflections/draft")
async def draft_reflection(body: DraftRequest, teacher: Teacher = Depends(current_teacher)) -> dict:
    """Let the assistant summarise the conversation into an editable reflection."""
    doc = await store.get(body.conversation_id, teacher.id)
    if doc is None or not doc.get("history"):
        raise HTTPException(status_code=404, detail="Conversation not found")
    ctx = await open_lesson(teacher, doc["lesson_id"])
    lesson = await ctx.lesson()
    await ctx.client.aclose()
    try:
        return await assistant.draft_reflection(store.history_from_doc(doc), int(lesson.get("minutes") or 1))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


@app.post("/reflections")
async def save_reflection(body: ReflectionIn, teacher: Teacher = Depends(current_teacher)) -> dict:
    """Save a (teacher-approved) reflection as a Tcherly bookmark with a question and optional action."""
    ctx = await open_lesson(teacher, body.lesson_id)
    try:
        lesson = await ctx.lesson()
        minutes = int(lesson.get("minutes") or 0)
        start = min(body.start_min, max(minutes - 1, 0))
        end = max(start + 1, min(body.end_min, minutes))
        states = [s for s in body.states if s in ("difficult", "easy", "boring", "engaging")]
        bookmark = await ctx.client.add_bookmark(
            str(lesson["_id"]),
            {
                "topic": body.topic,
                "time_from": start,
                "time_to": end,
                "feedback_type": states,
                "activated": ["net_difficult", "net_engaging"],
                "threshold": 0,
                "questions": [{"name": body.question, "action": ""}],
                "actions": [{"question": 0, "action": body.action, "future_action": ""}] if body.action.strip() else [],
            },
        )
    except TcherlyAPIError as error:
        raise HTTPException(status_code=error.status, detail=str(error))
    finally:
        await ctx.client.aclose()

    if body.conversation_id and body.proposal_id:
        await store.mark_proposal_saved(body.conversation_id, teacher.id, body.proposal_id, str(bookmark["_id"]))
    return {"success": True, "bookmark": bookmark}
