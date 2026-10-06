"""Lesson reports: a concise, shareable summary of a lesson's analytics and the teacher's reflections.

1. Python gathers the evidence deterministically (overview, the key moments and what students said
   in them, the teacher's saved reflections), so every report covers the same essentials.
2. One structured Gemini call writes the sections, citing evidence IDs.
3. The grounding check verifies every cited number, with one repair attempt if something doesn't match.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.genai import types

from . import analytics, grounding
from .assistant import TeachMate, extract_citations
from .config import settings
from .tcherly_client import TcherlyAPIError
from .tools import ToolContext

log = logging.getLogger("teachmate")

REPORT_INSTRUCTIONS = (Path(__file__).parent / "prompts" / "report.md").read_text(encoding="utf-8")
MAX_MOMENTS = 4
MIN_WINDOW = 2  # minutes; a single-minute peak gets a little context on each side

_TEXT = {"type": "string"}
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "The single most important finding, 1-2 cited sentences."},
        "at_a_glance": {"type": "array", "items": _TEXT, "description": "3-5 short cited facts."},
        "key_moments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "window": {"type": "string", "description": "Exactly as listed, e.g. 'min 16-22'."},
                    "title": {"type": "string", "description": "Short neutral label for what happened, max 8 words."},
                    "what_happened": {"type": "string", "description": "2-3 cited sentences."},
                    "students_said": {"type": "string", "description": "Reasons and students' own words, cited; empty if none."},
                },
                "required": ["window", "title", "what_happened", "students_said"],
            },
        },
        "what_worked": {"type": "array", "items": _TEXT},
        "reflections": {"type": "array", "items": _TEXT},
        "open_questions": {"type": "array", "items": _TEXT},
        "strategies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "option": {"type": "string", "description": "A small concrete option to adopt, adapt or reject."},
                    "based_on": {
                        "type": "string",
                        "description": (
                            "The 'Teaching strategy' evidence this option builds on: strategy name, its source in short and the "
                            "citation, e.g. 'Worked examples (Atkinson et al., 2000) [E36]'. Empty only if no strategy evidence fits."
                        ),
                    },
                    "addresses": {"type": "string", "description": "Which finding it responds to, cited."},
                    "check": {"type": "string", "description": "How the teacher could tell next time whether it helped."},
                },
                "required": ["option", "based_on", "addresses", "check"],
            },
        },
    },
    "required": ["headline", "at_a_glance", "key_moments", "what_worked", "reflections", "open_questions", "strategies"],
}

MOMENT_KINDS = (
    ("difficulty", "high", "most difficult"),
    ("engagement", "low", "most boring"),
    ("engagement", "high", "most engaging"),
    ("difficulty", "low", "easiest"),
)


def select_moments(series: list[dict], minutes: int) -> list[dict]:
    """The strongest peaks across the four signals, each widened to >= MIN_WINDOW minutes.

    Stronger peaks keep their exact windows. A weaker peak that lies mostly (>= half) inside a chosen
    window only adds its label there; one that overlaps less is skipped, so windows never overlap.
    """
    candidates = []
    for signal, direction, kind in MOMENT_KINDS:
        for moment in analytics.find_moments(series, signal, direction, top_k=2):
            candidates.append({**moment, "kind": kind, "strength": abs(moment["peak_value"])})
    candidates.sort(key=lambda m: m["strength"], reverse=True)

    chosen: list[dict] = []
    for moment in candidates:
        start, end = moment["start_min"], moment["end_min"]
        if end - start < MIN_WINDOW:
            start, end = max(0, start - 1), min(minutes, end + 1)
        overlaps = [(c, min(end, c["end_min"]) - max(start, c["start_min"])) for c in chosen]
        overlaps = [(c, size) for c, size in overlaps if size > 0]
        if overlaps:
            best, size = max(overlaps, key=lambda pair: pair[1])
            if size * 2 >= end - start and moment["kind"] not in best["kinds"]:
                best["kinds"].append(moment["kind"])
        elif len(chosen) < MAX_MOMENTS:
            chosen.append({"start_min": start, "end_min": end, "kinds": [moment["kind"]]})
    for moment in chosen:
        moment["window"] = analytics.window_label(moment["start_min"], moment["end_min"])
    return sorted(chosen, key=lambda m: m["start_min"])


async def gather(ctx: ToolContext) -> dict[str, Any]:
    """Collect all evidence for the report into ctx.evidence; return the lesson facts used in the header."""
    lesson = await ctx.lesson()
    minutes = int(lesson.get("minutes") or 0)
    full = await ctx.feedback_for(ctx.lesson_id, 0, minutes)
    feedback = full["feedback"]
    log_ = ctx.evidence

    analytics.lesson_overview(log_, full["lesson"], feedback)
    moments = select_moments(analytics.minute_series(feedback), minutes)
    labels = await ctx.client.reason_labels()
    for moment in moments:
        segment = await ctx.feedback_for(ctx.lesson_id, moment["start_min"], moment["end_min"])
        analytics.segment_analytics(log_, segment["lesson"], segment["feedback"], moment["start_min"], moment["end_min"], labels)
    analytics.reflections(log_, lesson)
    try:  # viewing behaviour (re-watching, skipping, reach) supports or questions the feedback
        analytics.viewing_behaviour(log_, await ctx.client.behaviour(ctx.lesson_id), feedback)
    except TcherlyAPIError as error:
        log.warning("no viewing behaviour for the report: %s", error)

    # RAG: strategies (and the teacher's own past reflections) matching what students said about the hard parts.
    problem_windows = [m["window"] for m in moments if {"most difficult", "most boring"} & set(m["kinds"])]
    reasons = [
        e.fact
        for e in log_.items
        if e.source == "segment" and "reason selections" in e.fact and any(e.fact.startswith(w + ":") for w in problem_windows)
    ]
    if reasons:
        try:
            await ctx.retrieve_knowledge("Students found parts of this lecture difficult or boring. " + " ".join(reasons)[:1500], top_k=4)
        except (TcherlyAPIError, RuntimeError, ValueError) as error:
            log.warning("no teaching strategies for the report: %s", error)

    course_name = None
    if lesson.get("course"):
        try:
            course_name = (await ctx.client.course(str(lesson["course"]))).get("name")
        except TcherlyAPIError:
            pass

    watched = len(lesson.get("watched") or [])
    responders = feedback.get("students_count", 0)
    unique = feedback.get("unique", {})
    stats = {
        "lesson": lesson.get("name"),
        "course": course_name,
        "minutes": minutes,
        "watched": watched,
        "responders": responders,
        "participation_pct": analytics.pct(responders, watched),
        "states": {state: unique.get(state, 0) for state in analytics.STATES},
        "bookmarks": len([b for b in lesson.get("bookmarks") or [] if isinstance(b, dict)]),
        # Per-minute net values as on the dashboard line chart: [minute, net difficulty, net engagement]
        "series": [[m["minute"], m["net_difficult"], m["net_engagement"]] for m in analytics.minute_series(feedback)],
    }
    return {"lesson": lesson, "stats": stats, "moments": moments}


def report_text(sections: dict[str, Any]) -> str:
    """All written text, one item per line, for the grounding check."""
    lines = [sections.get("headline", "")]
    lines += sections.get("at_a_glance", [])
    for moment in sections.get("key_moments", []):
        lines += [moment.get("what_happened", ""), moment.get("students_said", "")]
    lines += sections.get("what_worked", []) + sections.get("reflections", []) + sections.get("open_questions", [])
    for strategy in sections.get("strategies", []):
        lines += [strategy.get("option", ""), strategy.get("based_on", ""), strategy.get("addresses", ""), strategy.get("check", "")]
    return "\n".join(line for line in lines if line)


def _prompt(stats: dict[str, Any], moments: list[dict], evidence: analytics.EvidenceLog) -> str:
    moment_lines = "\n".join(f"- {m['window']} ({', '.join(m['kinds'])})" for m in moments) or "- none (very little feedback)"
    evidence_lines = "\n".join(f"{e.id}: {e.fact}" for e in evidence.items)
    return (
        f"{REPORT_INSTRUCTIONS}\n\n"
        f"### Lesson\n'{stats['lesson']}'"
        + (f" in course '{stats['course']}'" if stats.get("course") else "")
        + f", {stats['minutes']} minutes long.\n\n"
        f"### Key moments selected\n{moment_lines}\n\n"
        f"### Evidence\n{evidence_lines}\n\nReturn the report as JSON."
    )


async def generate(assistant: TeachMate, ctx: ToolContext) -> dict[str, Any]:
    gathered = await gather(ctx)
    stats, moments = gathered["stats"], gathered["moments"]

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=_prompt(stats, moments, ctx.evidence))])]
    sections, model = await assistant.generate_json(contents, SCHEMA, purpose="write the report", timeout_s=settings.report_timeout_s)
    check = grounding.check(report_text(sections), ctx.evidence)
    repaired = False

    if not check.grounded:
        log.info("report grounding issues (%s); asking for one repair", check.score)
        fix = (
            "[Automatic grounding check] Some statements in this report don't match the evidence they cite:\n"
            + check.feedback_for_model()
            + "\n\nReturn the whole report as JSON again, correcting only these statements (fix the number or the "
            "citation, or remove the claim). Keep everything else unchanged.\n\nReport:\n"
            + json.dumps(sections, ensure_ascii=False)
        )
        try:
            fixed, fixed_model = await assistant.generate_json(
                contents + [types.Content(role="user", parts=[types.Part.from_text(text=fix)])],
                SCHEMA,
                purpose="correct the report",
                timeout_s=settings.report_timeout_s,
            )
            fixed_check = grounding.check(report_text(fixed), ctx.evidence)
            if fixed_check.score >= check.score:
                sections, check, model, repaired = fixed, fixed_check, fixed_model, True
        except RuntimeError as error:  # keep the first version; its grounding result is shown to the teacher
            log.warning("report repair failed: %s", error)

    cited = extract_citations(report_text(sections))
    return {
        "lesson_id": str(gathered["lesson"]["_id"]),
        "lesson_slug": gathered["lesson"].get("id"),
        "created_at": datetime.now(timezone.utc),
        "model": model,
        "stats": stats,
        "moments": moments,
        "sections": sections,
        "citations": {cid: e.fact for cid in cited if (e := ctx.evidence.get(cid))},
        "evidence": [e.as_dict() for e in ctx.evidence.items],
        "grounding": check.as_dict(),
        "repaired": repaired,
    }
