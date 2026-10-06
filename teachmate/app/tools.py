"""Tools the assistant can call. Each returns numbered evidence items built by analytics.py."""
import json
import uuid
from typing import Any

from google.genai import types

from . import analytics, knowledge
from .analytics import EvidenceLog
from .tcherly_client import TcherlyAPIError, TcherlyClient

# Past reflections are shortlisted by semantic similarity (at most MAX_PAST_REFLECTIONS above a loose floor) and
# offered as "possibly related"; the model decides whether one really addresses the same kind of problem.
# Raw scores alone are too close to separate related from unrelated reflections reliably.
REFLECTION_MATCH = 0.80
MAX_PAST_REFLECTIONS = 2

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "get_lesson_overview",
        "description": (
            "Whole-lecture summary of the current lesson: participation, how many students reported each state, "
            "the per-minute net difficulty / net engagement series shown on the dashboard, the most difficult, easiest, "
            "most engaging and most boring moments, and the largest engagement drop. Call this first for broad questions."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_segment_analytics",
        "description": (
            "Detailed analytics for one time window of the current lesson: share of students reporting each state, "
            "Venn overlaps (students reporting two states), average net values, and the reasons students gave "
            "(including their own free-text words). Use it to explain WHY a moment was difficult/boring/engaging."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_min": {"type": "integer", "description": "Window start in minutes of video time (e.g. 16 for 16:00)."},
                "end_min": {"type": "integer", "description": "Window end in minutes of video time (e.g. 22 for 22:00)."},
            },
            "required": ["start_min", "end_min"],
        },
    },
    {
        "name": "find_moments",
        "description": "Find the time windows where a signal peaks, e.g. the most difficult or the most boring parts of the lesson.",
        "parameters": {
            "type": "object",
            "properties": {
                "signal": {"type": "string", "enum": ["difficulty", "engagement"]},
                "direction": {
                    "type": "string",
                    "enum": ["high", "low"],
                    "description": "high = most difficult / most engaging; low = easiest / most boring.",
                },
                "top_k": {"type": "integer", "description": "How many windows to return (1-5).", "default": 3},
            },
            "required": ["signal", "direction"],
        },
    },
    {
        "name": "compare_course_lessons",
        "description": (
            "Compare all lessons in the current lesson's course (participation, average net difficulty/engagement, "
            "share of 'struggle minutes'). Use for questions like 'which video needs revision?'."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_viewing_behaviour",
        "description": (
            "How students WATCHED the video, from the player logs: where they jumped back to re-watch, where they "
            "skipped ahead, pause totals, and how far they got (who reached the end). Each hotspot comes with the "
            "chart values at that minute. Use it to strengthen or question what the feedback shows, e.g. whether a "
            "difficult part was also re-watched. Without start_min/end_min it covers the whole lecture."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_min": {"type": "integer", "description": "Optional window start in video minutes."},
                "end_min": {"type": "integer", "description": "Optional window end in video minutes."},
            },
        },
    },
    {
        "name": "get_teacher_reflections",
        "description": "The teacher's own saved bookmarks, questions and actions for the current lesson (their earlier reflections).",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "find_teaching_strategies",
        "description": (
            "Search TeachMate's library of research-based teaching strategies (each with its source) and the teacher's "
            "own saved reflections from their OTHER lessons. Call it BEFORE suggesting options, in-class activities or "
            "changes, with a one-line description of the problem as students experienced it (what they reported and why), "
            "e.g. 'students found the loop demonstration too fast and the code too small to read'. Build suggestions on "
            "what it returns and cite it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "problem": {"type": "string", "description": "The problem in students' terms: feedback, reasons, behaviour."},
                "top_k": {"type": "integer", "description": "How many strategies to return (1-5).", "default": 3},
            },
            "required": ["problem"],
        },
    },
    {
        "name": "propose_reflection",
        "description": (
            "Offer the teacher a reflection to save in Tcherly as a bookmark (time window + reflective question + optional action). "
            "Nothing is saved automatically: the teacher sees an editable card and decides. Use it when the teacher reaches a "
            "conclusion, decides on something to try, or asks you to remember/save something. Word the question and action "
            "from the teacher's perspective, using their own conclusions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Short name of the segment or concept, max 60 characters."},
                "start_min": {"type": "integer"},
                "end_min": {"type": "integer"},
                "states": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["difficult", "easy", "boring", "engaging"]},
                    "description": "The feedback states this reflection is about.",
                },
                "question": {"type": "string", "description": "The reflective question or finding, in the teacher's voice."},
                "action": {"type": "string", "description": "What the teacher plans to try or has done. Empty if they haven't decided."},
            },
            "required": ["topic", "start_min", "end_min", "states", "question"],
        },
    },
]


def gemini_tools() -> list[types.Tool]:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(name=s["name"], description=s["description"], parameters_json_schema=s["parameters"])
                for s in TOOL_SPECS
            ]
        )
    ]


class ToolContext:
    """Per-conversation state: which lesson, the Node API client, cached responses and the evidence log."""

    def __init__(self, client: TcherlyClient, lesson_id: str, evidence: EvidenceLog | None = None):
        self.client = client
        self.lesson_id = lesson_id
        self.evidence = evidence or EvidenceLog()
        # Reflections the assistant proposed this session; saved only when the teacher confirms in the UI.
        self.proposals: list[dict[str, Any]] = []
        self._turn_start = 0
        self._feedback_cache: dict[tuple[str, int, int], dict] = {}
        self._lesson: dict | None = None
        self._other_reflections: list[dict] | None = None

    async def lesson(self) -> dict:
        if self._lesson is None:
            self._lesson = (await self.feedback_for(self.lesson_id))["lesson"]
        return self._lesson

    async def feedback_for(self, lesson_id: str, start_min: int = 0, end_min: int | None = None) -> dict:
        if end_min is None:
            # Minutes aren't known before the first call; the Node API caps ranges at the lesson length.
            end_min = 10_000
        key = (lesson_id, start_min, end_min)
        if key not in self._feedback_cache:
            self._feedback_cache[key] = await self.client.feedback(lesson_id, start_min, end_min)
        return self._feedback_cache[key]

    async def run(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        try:
            if name == "propose_reflection":
                return await self._propose(args)
            items = await self._dispatch(name, args)
            return {"evidence": [e.as_dict() for e in items]}
        except TcherlyAPIError as error:
            return {"error": str(error)}
        except (KeyError, ValueError, TypeError) as error:
            return {"error": f"invalid arguments for {name}: {error}"}

    async def _dispatch(self, name: str, args: dict[str, Any]) -> list[analytics.Evidence]:
        log = self.evidence
        lesson = await self.lesson()
        minutes = int(lesson.get("minutes") or 0)

        if name == "get_lesson_overview":
            data = await self.feedback_for(self.lesson_id, 0, minutes)
            return analytics.lesson_overview(log, data["lesson"], data["feedback"])

        if name == "get_segment_analytics":
            start = max(0, min(int(args["start_min"]), minutes - 1))
            end = max(start + 1, min(int(args["end_min"]), minutes))
            data = await self.feedback_for(self.lesson_id, start, end)
            labels = await self.client.reason_labels()
            return analytics.segment_analytics(log, data["lesson"], data["feedback"], start, end, labels)

        if name == "find_moments":
            signal, direction = args["signal"], args["direction"]
            if signal not in analytics.SIGNALS or direction not in ("high", "low"):
                raise ValueError("signal must be difficulty|engagement and direction high|low")
            top_k = max(1, min(int(args.get("top_k", 3)), 5))
            data = await self.feedback_for(self.lesson_id, 0, minutes)
            return analytics.moments(log, data["feedback"], signal, direction, top_k)

        if name == "compare_course_lessons":
            course_id = lesson.get("course")
            if not course_id:
                raise ValueError("this lesson is not part of a course")
            course = await self.client.course(str(course_id))
            rows = []
            for other in course.get("lessons", []):
                data = await self.feedback_for(other["_id"], 0, int(other.get("minutes") or 0))
                if data["feedback"].get("students_count"):
                    rows.append(analytics.lesson_summary_row(data["lesson"], data["feedback"]))
            return analytics.compare_lessons(log, course.get("name", "this course"), rows)

        if name == "get_viewing_behaviour":
            data = await self.feedback_for(self.lesson_id, 0, minutes)
            if args.get("start_min") is not None and args.get("end_min") is not None:
                start = max(0, min(int(args["start_min"]), minutes - 1))
                end = max(start + 1, min(int(args["end_min"]), minutes))
                behaviour = await self.client.behaviour(self.lesson_id, start, end)
                return analytics.viewing_behaviour(log, behaviour, data["feedback"], start, end)
            behaviour = await self.client.behaviour(self.lesson_id)
            return analytics.viewing_behaviour(log, behaviour, data["feedback"])

        if name == "find_teaching_strategies":
            problem = str(args["problem"]).strip()
            if not problem:
                raise ValueError("describe the problem to search for")
            return await self.retrieve_knowledge(problem, max(1, min(int(args.get("top_k", 3)), 5)))

        if name == "get_teacher_reflections":
            # `lesson` comes from the owner-checked feedback endpoint and has bookmarks populated.
            return analytics.reflections(log, lesson)

        raise ValueError(f"unknown tool {name}")

    async def other_reflections(self, max_lessons: int = 30) -> list[dict]:
        """The teacher's saved reflections (bookmark questions/actions) from their other lessons."""
        if self._other_reflections is not None:
            return self._other_reflections
        lesson = await self.lesson()
        items: list[dict] = []
        scanned = 0
        for course in await self.client.courses():
            full = await self.client.course(str(course["_id"]))
            for other in full.get("lessons", []):
                if str(other.get("_id")) == str(lesson.get("_id")) or not other.get("bookmarks") or scanned >= max_lessons:
                    continue
                scanned += 1
                detail = await self.client.lesson(other.get("id") or str(other["_id"]))
                for bookmark in detail.get("bookmarks") or []:
                    if not isinstance(bookmark, dict):
                        continue
                    questions = [q.get("name") for q in bookmark.get("questions", []) if q.get("name")]
                    actions = [a.get("action") or a.get("future_action") for a in bookmark.get("actions", []) if a.get("action") or a.get("future_action")]
                    if questions or actions:
                        items.append(
                            {
                                "lesson": detail.get("name", ""),
                                "window": analytics.window_label(bookmark.get("time_from", 0), bookmark.get("time_to", 0)),
                                "topic": bookmark.get("topic") or "",
                                "questions": questions,
                                "actions": actions,
                            }
                        )
        self._other_reflections = items
        return items

    async def retrieve_knowledge(self, problem: str, top_k: int = 3) -> list[analytics.Evidence]:
        """RAG: best-matching strategy notes plus the teacher's matching reflections from other lessons."""
        reflections = await self.other_reflections()
        texts = [f"{r['topic']}. {' '.join(r['questions'])} {' '.join(r['actions'])}" for r in reflections]
        result = await knowledge.library().search(problem, top_k=top_k, extra_texts=texts)
        threshold = REFLECTION_MATCH if result["method"] == "embeddings" else 0.01
        matched = sorted(((score, r) for score, r in zip(result["extra"], reflections) if score >= threshold), key=lambda p: -p[0])
        return analytics.strategies(self.evidence, result["notes"], result["method"]) + analytics.past_reflections(
            self.evidence, [r for _, r in matched[:MAX_PAST_REFLECTIONS]]
        )

    def begin_turn(self) -> None:
        self._turn_start = len(self.proposals)

    async def _propose(self, args: dict[str, Any]) -> dict[str, Any]:
        lesson = await self.lesson()
        minutes = int(lesson.get("minutes") or 0)
        start = max(0, min(int(args["start_min"]), minutes - 1))
        states = [s for s in args.get("states") or [] if s in analytics.STATES]
        proposal = {
            "id": uuid.uuid4().hex[:12],
            "topic": str(args["topic"])[:60],
            "start_min": start,
            "end_min": max(start + 1, min(int(args["end_min"]), minutes)),
            "states": states,
            "question": str(args["question"]),
            "action": str(args.get("action") or ""),
            "status": "proposed",
        }
        if len(self.proposals) > self._turn_start:
            # One card per turn: a second call refines the card already shown.
            proposal["id"] = self.proposals[-1]["id"]
            self.proposals[-1] = proposal
        else:
            self.proposals.append(proposal)
        return {"status": "shown to the teacher as an editable card; it is saved only if they click Save", "proposal": proposal}


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
