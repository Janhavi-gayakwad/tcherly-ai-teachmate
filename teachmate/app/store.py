"""MongoDB persistence for TeachMate conversations (collection `teachmate_conversations`).

A conversation stores the visible messages (for the UI and reports), the Gemini
content history (to continue the conversation), the evidence log (so citations
still resolve after a reload) and any reflections proposed or saved.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from google.genai import types
from pymongo import AsyncMongoClient, DESCENDING

from .analytics import Evidence, EvidenceLog
from .config import settings

_client = AsyncMongoClient(settings.mongo_uri, tz_aware=True)
_db = _client.get_default_database("test-debe")
conversations = _db["teachmate_conversations"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes() -> None:
    await conversations.create_index([("teacher_id", 1), ("lesson_id", 1), ("updated_at", DESCENDING)])


def evidence_from_doc(doc: dict) -> EvidenceLog:
    return EvidenceLog(items=[Evidence(**item) for item in doc.get("evidence", [])])


def history_from_doc(doc: dict) -> list[types.Content]:
    return [types.Content.model_validate(c) for c in doc.get("history", [])]


async def create(teacher_id: str, lesson: dict) -> dict:
    doc = {
        "_id": uuid.uuid4().hex,
        "teacher_id": teacher_id,
        "lesson_id": str(lesson["_id"]),
        "lesson_slug": lesson.get("id"),
        "lesson_name": lesson.get("name"),
        "title": None,
        "created_at": _now(),
        "updated_at": _now(),
        "messages": [],
        "history": [],
        "evidence": [],
        "proposals": [],
    }
    await conversations.insert_one(doc)
    return doc


async def get(conversation_id: str, teacher_id: str) -> dict | None:
    return await conversations.find_one({"_id": conversation_id, "teacher_id": teacher_id})


async def list_for_lesson(teacher_id: str, lesson_id: str, limit: int = 20) -> list[dict]:
    cursor = conversations.find(
        {"teacher_id": teacher_id, "lesson_id": lesson_id},
        {"title": 1, "created_at": 1, "updated_at": 1, "messages": {"$slice": -1}},
    ).sort("updated_at", DESCENDING).limit(limit)
    return [doc async for doc in cursor]


async def save_turn(
    doc: dict,
    teacher_message: str,
    assistant_message: dict[str, Any],
    history: list[types.Content],
    evidence: EvidenceLog,
    proposals: list[dict],
) -> None:
    now = _now()
    update: dict[str, Any] = {
        "$push": {
            "messages": {
                "$each": [
                    {"role": "teacher", "text": teacher_message, "at": now},
                    {"role": "assistant", "at": now, **assistant_message},
                ]
            }
        },
        "$set": {
            "updated_at": now,
            "history": [c.model_dump(mode="json", exclude_none=True) for c in history],
            "evidence": [{"id": e.id, "fact": e.fact, "data": e.data, "source": e.source} for e in evidence.items],
        },
    }
    if not doc.get("title"):
        update["$set"]["title"] = teacher_message[:80]
    if proposals:
        update["$push"]["proposals"] = {"$each": proposals}
    await conversations.update_one({"_id": doc["_id"]}, update)


async def mark_proposal_saved(conversation_id: str, teacher_id: str, proposal_id: str, bookmark_id: str) -> None:
    await conversations.update_one(
        {"_id": conversation_id, "teacher_id": teacher_id, "proposals.id": proposal_id},
        {"$set": {"proposals.$.status": "saved", "proposals.$.bookmark_id": bookmark_id, "proposals.$.saved_at": _now()}},
    )
