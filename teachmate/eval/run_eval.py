"""Evaluate TeachMate on a fixed set of teacher questions, the report generator and the grounding check.

Run from the project folder, with the Node server running, the demo data seeded (`npm run seed`) and
GEMINI_API_KEY set:

    teachmate/.venv/Scripts/python teachmate/eval/run_eval.py              (Windows)
    teachmate/.venv/bin/python teachmate/eval/run_eval.py                  (macOS/Linux)

Options:
    --judge          also let Gemini rate each answer 1-5 (non-directive, reflective, evidence use, usefulness)
    --reports        also generate and check one report per demo lesson
    --only J1,P2     run only these question ids
    --pause 4        seconds between questions (free-tier rate limits)
    --resume DIR     continue an earlier run in DIR (questions that already succeeded are skipped)

TeachMate is called in-process (same code path as the API, real Node data via the teacher's token), so the
evaluation doesn't add conversations or reports to the demo teacher's history.
Results: teachmate/eval/results/<timestamp>/ with results.json, results.csv and summary.md.
"""
import argparse
import asyncio
import csv
import json
import re
import statistics
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))  # teachmate/, so `app` imports work

from app import report as reports  # noqa: E402
from app.assistant import TeachMate  # noqa: E402
from app.config import settings  # noqa: E402
from app.tcherly_client import TcherlyClient, sign_in  # noqa: E402
from app.tools import ToolContext  # noqa: E402

import grounding_cases  # noqa: E402

DIRECTIVE = re.compile(
    r"\byou (?:should|must|need to|have to|ought to)\b|\bmake sure (?:you|to)\b|\bit is (?:essential|necessary) (?:that|to)\b",
    re.IGNORECASE,
)
# A flat verdict: the answer opens with "Yes," / "No." or calls the lecture bad outright.
VERDICT = re.compile(r"^\W*(?:yes|no)\s*[,.!:;—–-]|\bthis (?:lecture|video|lesson) is (?:bad|poor|terrible|a failure)\b", re.IGNORECASE)
JUDGE_SYSTEM = (
    "You evaluate answers from TeachMate, an AI assistant that helps university teachers reflect on their class's "
    "lecture feedback. Its intended behaviour: support the teacher's own reasoning (Schon's reflective practice) "
    "rather than instructing them; ground claims in the class data it cites; ask the teacher reflective questions; "
    "offer options to adopt, adapt or reject, never orders; be honest about the limits of the data; stay on topic. "
    "Rate strictly. 5 = excellent, 3 = acceptable with clear weaknesses, 1 = poor."
)
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "non_directive": {"type": "integer", "description": "Supports the teacher's judgement instead of telling them what to do (1-5)."},
        "reflective": {"type": "integer", "description": "Prompts genuine reflection with specific, open questions (1-5)."},
        "evidence_use": {"type": "integer", "description": "Grounds its claims in the class data and is honest about its limits (1-5)."},
        "usefulness": {"type": "integer", "description": "Helps a busy teacher understand the situation and decide what to explore next (1-5)."},
        "comment": {"type": "string", "description": "One sentence explaining the scores."},
    },
    "required": ["non_directive", "reflective", "evidence_use", "usefulness", "comment"],
}
JUDGE_KEYS = ["non_directive", "reflective", "evidence_use", "usefulness"]


def mentions(text: str, keyword: str) -> bool:
    if keyword.isdigit():
        return re.search(rf"(?<![\d.]){keyword}(?![\d.])", text) is not None
    return keyword.lower() in text.lower()


def reflective_questions(text: str) -> int:
    """Questions addressed to the teacher: sentences or bullets ending in '?' that mention you/your."""
    candidates = re.split(r"(?<=[?.!])\s+|\n", text)
    return sum(1 for c in candidates if c.strip().endswith("?") and re.search(r"\byou(r)?\b", c, re.IGNORECASE))


def text_metrics(question: dict, text: str) -> dict:
    """Metrics computed from the answer text alone (re-applied to earlier rows on --resume)."""
    verdict = question["category"] == "Pressure for a verdict" and VERDICT.search(text[:200])
    return {
        "reflective_questions": reflective_questions(text),
        "has_reflective_question": reflective_questions(text) > 0,
        "directive_phrases": DIRECTIVE.findall(text),
        "non_directive": not DIRECTIVE.search(text) and not verdict,
        "key_content": any(mentions(text, k) for k in question.get("expect_any", [])),
    }


async def ask(assistant: TeachMate, client: TcherlyClient, question: dict) -> dict:
    ctx = ToolContext(client, question["lesson"])
    started = time.perf_counter()
    turn = await assistant.reply(ctx, question["question"])
    seconds = round(time.perf_counter() - started, 1)
    text = turn.text
    tools = [c["name"] for c in turn.tool_calls]
    strategy_ids = [cid for cid in turn.cited if (e := ctx.evidence.get(cid)) and e.source == "knowledge"]
    expect_tools = question.get("expect_tools") or []
    return {
        "id": question["id"],
        "lesson": question["lesson"],
        "category": question["category"],
        "question": question["question"],
        "answer": text,
        "model": turn.model,
        "fallback_used": turn.model != settings.gemini_models[0],
        "seconds": seconds,
        "tools": tools,
        "tool_calls": turn.tool_calls,
        "grounded": turn.grounding.get("grounded"),
        "grounding_score": turn.grounding.get("score"),
        "numbers_checked": turn.grounding.get("checked_numbers"),
        "grounding_issues": turn.grounding.get("unsupported", []) + [{"unknown_id": i} for i in turn.grounding.get("unknown_ids", [])],
        "repaired": turn.repaired,
        "citations": len(turn.cited),
        "evidence_backed": len(turn.cited) > 0,
        **text_metrics(question, text),
        "right_tool": (any(t in tools for t in expect_tools) if expect_tools else None),
        "strategy_citations": len(strategy_ids),
        "proposal_made": bool(turn.proposals),
        "error": None,
    }


async def judge(assistant: TeachMate, row: dict) -> dict:
    from google.genai import types

    prompt = f"Teacher's question:\n{row['question']}\n\nTeachMate's answer:\n{row['answer']}\n\nRate the answer."
    data, model = await assistant.generate_json(
        [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])], JUDGE_SCHEMA, purpose="judge an answer", system=JUDGE_SYSTEM
    )
    return {**{k: max(1, min(5, int(data[k]))) for k in JUDGE_KEYS}, "comment": data.get("comment", ""), "judge_model": model}


async def check_report(assistant: TeachMate, client: TcherlyClient, lesson: str) -> dict:
    ctx = ToolContext(client, lesson)
    started = time.perf_counter()
    result = await reports.generate(assistant, ctx)
    sections = result["sections"]
    strategies = sections.get("strategies", [])
    knowledge_ids = {e.id for e in ctx.evidence.items if e.source == "knowledge"}
    based = [s for s in strategies if any(f"E{n}" in knowledge_ids for n in re.findall(r"E(\d+)", s.get("based_on", "")))]
    return {
        "lesson": lesson,
        "seconds": round(time.perf_counter() - started, 1),
        "model": result["model"],
        "grounded": result["grounding"]["grounded"],
        "grounding_score": result["grounding"]["score"],
        "numbers_checked": result["grounding"]["checked_numbers"],
        "repaired": result["repaired"],
        "key_moments": len(sections.get("key_moments", [])),
        "open_questions": len(sections.get("open_questions", [])),
        "strategies": len(strategies),
        "strategies_based_on_library": len(based),
        "directive_phrases": DIRECTIVE.findall(json.dumps(sections)),
    }


def pct(values: list) -> str:
    values = [v for v in values if v is not None]
    return f"{round(100 * sum(1 for v in values if v) / len(values))}% ({sum(1 for v in values if v)}/{len(values)})" if values else "n/a"


def write_outputs(out: Path, results: dict) -> None:
    (out / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    rows = results["questions"]
    fields = ["id", "lesson", "category", "seconds", "model", "fallback_used", "tools", "grounded", "grounding_score", "numbers_checked",
              "repaired", "citations", "has_reflective_question", "non_directive", "right_tool", "key_content", "strategy_citations",
              "proposal_made", "error"] + [f"judge_{k}" for k in JUDGE_KEYS]
    with open(out / "results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flat = {**row, "tools": " ".join(row.get("tools", [])), **{f"judge_{k}": (row.get("judge") or {}).get(k) for k in JUDGE_KEYS}}
            writer.writerow(flat)
    (out / "summary.md").write_text(summary_markdown(results), encoding="utf-8")


def summary_markdown(results: dict) -> str:
    rows = [r for r in results["questions"] if not r.get("error")]
    errors = [r for r in results["questions"] if r.get("error")]
    lines = [
        "# TeachMate evaluation",
        "",
        f"Run: {results['started']}. Models (in fallback order): {', '.join(results['models'])}. "
        f"Questions answered: {len(rows)} of {len(results['questions'])}" + (f" ({len(errors)} failed, see below)" if errors else "") + ".",
        "",
        "The demo data is synthetic (seeded from the patterns in Chavan & Mitra, 2022). Metrics are automatic heuristics; see Notes.",
        "",
        "## Overall",
        "",
        "| Metric | Result |",
        "| --- | --- |",
        f"| Grounded (every cited number matches its evidence) | {pct([r['grounded'] for r in rows])} |",
        f"| Mean grounding score | {round(statistics.mean(r['grounding_score'] for r in rows), 3) if rows else 'n/a'} |",
        f"| Numbers checked in total | {sum(r['numbers_checked'] or 0 for r in rows)} |",
        f"| Answers repaired by the grounding check | {pct([r['repaired'] for r in rows])} |",
        f"| Evidence-backed (cites at least one evidence item) | {pct([r['evidence_backed'] for r in rows if r['category'] != 'Off-topic'])} |",
        f"| Asks the teacher a reflective question | {pct([r['has_reflective_question'] for r in rows if r['category'] != 'Off-topic'])} |",
        f"| Non-directive (no 'you should/must', no yes/no verdict) | {pct([r['non_directive'] for r in rows])} |",
        f"| Used the expected tool | {pct([r['right_tool'] for r in rows])} |",
        f"| Mentions the key content | {pct([r['key_content'] for r in rows])} |",
        f"| Activity/strategy answers citing the strategy library | {pct([r['strategy_citations'] > 0 for r in rows if r['category'] == 'In-class activities'])} |",
        f"| Response time: median / max (s) | {statistics.median(r['seconds'] for r in rows) if rows else 'n/a'} / {max((r['seconds'] for r in rows), default='n/a')} |",
        f"| Answered by a fallback model (main model busy) | {pct([r['fallback_used'] for r in rows])} |",
        f"| Answers by model | {', '.join(f'{m}: {n}' for m, n in sorted(Counter(r['model'] for r in rows).items()))} |",
    ]
    judged = [r for r in rows if r.get("judge")]
    if judged:
        lines += [f"| AI judge, mean {k.replace('_', ' ')} (1-5) | {round(statistics.mean(r['judge'][k] for r in judged), 2)} |" for k in JUDGE_KEYS]

    categories = sorted({r["category"] for r in rows})
    lines += ["", "## By question type", "", "| Type | Questions | Grounded | Reflective question | Non-directive | Expected tool | Key content |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for cat in categories:
        cr = [r for r in rows if r["category"] == cat]
        lines.append(f"| {cat} | {len(cr)} | {pct([r['grounded'] for r in cr])} | {pct([r['has_reflective_question'] for r in cr])} | {pct([r['non_directive'] for r in cr])} | {pct([r['right_tool'] for r in cr])} | {pct([r['key_content'] for r in cr])} |")

    yes = lambda v: "n/a" if v is None else ("yes" if v else "**no**")  # noqa: E731  (pass/fail columns)
    plain = lambda v: "yes" if v else "no"  # noqa: E731  (neutral columns)
    lines += ["", "## Each question", "", "| ID | Type | Question | Time (s) | Grounded | Reflective Q | Non-directive | Tool | Key content" + (" | Judge (ND/R/E/U)" if judged else "") + " |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | ---" + (" | ---" if judged else "") + " |"]
    for r in results["questions"]:
        if r.get("error"):
            lines.append(f"| {r['id']} | {r['category']} | {r['question']} | - | error: {r['error'][:60]} | | | | |")
            continue
        j = r.get("judge")
        judge_cell = f" | {j['non_directive']}/{j['reflective']}/{j['evidence_use']}/{j['usefulness']}" if j else (" | -" if judged else "")
        lines.append(
            f"| {r['id']} | {r['category']} | {r['question']} | {r['seconds']} | {yes(r['grounded'])} ({r['grounding_score']}) | "
            f"{yes(r['has_reflective_question'])} | {yes(r['non_directive'])} | {yes(r['right_tool'])} | {yes(r['key_content'])}{judge_cell} |"
        )

    if results.get("reports"):
        lines += ["", "## Lesson reports", "", "| Lesson | Time (s) | Model | Grounded | Numbers checked | Repaired | Key moments | Options based on the library | Directive phrases |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in results["reports"]:
            if r.get("error"):
                lines.append(f"| {r['lesson']} | - | - | error: {r['error'][:60]} | | | | | |")
                continue
            lines.append(f"| {r['lesson']} | {r['seconds']} | {r['model']} | {yes(r['grounded'])} ({r['grounding_score']}) | {r['numbers_checked']} | "
                         f"{plain(r['repaired'])} | {r['key_moments']} | {r['strategies_based_on_library']} of {r['strategies']} | {len(r['directive_phrases'])} |")

    cases = results["grounding_cases"]
    normal = [c for c in cases if not c["known_limitation"]]
    lines += [
        "",
        "## Grounding check on known cases",
        "",
        f"Correct verdicts on normal cases: {sum(c['correct'] for c in normal)} of {len(normal)} "
        f"(faulty answers caught: {sum(c['correct'] for c in normal if c['should_flag'])} of {sum(1 for c in normal if c['should_flag'])}; "
        f"false alarms: {sum(1 for c in normal if c['flagged'] and not c['should_flag'])}).",
        "",
        "| Case | Should flag | Flagged | Correct |",
        "| --- | --- | --- | --- |",
    ]
    lines += [f"| {c['case']}{' (known limitation)' if c['known_limitation'] else ''} | {plain(c['should_flag'])} | {plain(c['flagged'])} | {yes(c['correct'])} |" for c in cases]

    if errors:
        lines += ["", "## Failed questions", ""] + [f"- {r['id']}: {r['error']}" for r in errors]
    lines += [
        "",
        "## Notes",
        "",
        "- Reflective question: a sentence ending in '?' addressed to the teacher (contains you/your).",
        "- Non-directive: no 'you should / must / need to / have to' or 'make sure'; for the verdict question, also no flat 'Yes,' or 'No.' at the start.",
        "- Key content: the answer mentions at least one expected element (e.g. the minute or topic the data points to).",
        "- The grounding check verifies numbers against cited evidence. Known limitations (see the cases above): it cannot detect a "
        "correct number used with the wrong meaning, and it flags correct numbers the model derived itself (e.g. a window's length).",
        "- The AI judge (if used) is a Gemini model rating TeachMate's own model family; treat its scores as indicative, not independent.",
        "- Free-tier Gemini is often overloaded, so response times and the model that answers vary between runs.",
    ]
    return "\n".join(lines) + "\n"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate TeachMate.")
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--reports", action="store_true")
    parser.add_argument("--only", default="")
    parser.add_argument("--pause", type=float, default=4.0)
    parser.add_argument("--resume", default="")
    parser.add_argument("--email", default="demo.teacher@tcherly.local")
    parser.add_argument("--password", default="Demo@1234")
    args = parser.parse_args()

    questions = json.loads((EVAL_DIR / "questions.json").read_text(encoding="utf-8"))
    if args.only:
        wanted = set(args.only.split(","))
        questions = [q for q in questions if q["id"] in wanted]

    out = Path(args.resume) if args.resume else EVAL_DIR / "results" / datetime.now().strftime("%Y-%m-%d_%H%M")
    out.mkdir(parents=True, exist_ok=True)
    previous = json.loads((out / "results.json").read_text(encoding="utf-8")) if (out / "results.json").exists() else {}
    done = {r["id"]: r for r in previous.get("questions", []) if not r.get("error")}
    results = {
        "started": previous.get("started", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "models": settings.gemini_models,
        "questions": [],
        "reports": previous.get("reports", []),
        "grounding_cases": grounding_cases.run(),
    }

    assistant = TeachMate()
    client = TcherlyClient(await sign_in(args.email, args.password))
    try:
        for i, question in enumerate(questions, 1):
            if question["id"] in done:
                row = {**done[question["id"]], **text_metrics(question, done[question["id"]]["answer"])}
                if args.judge and not row.get("judge"):
                    row["judge"] = await judge(assistant, row)
                results["questions"].append(row)
                print(f"[{i}/{len(questions)}] {question['id']} already done")
                continue
            for attempt in range(3):
                try:
                    row = await ask(assistant, client, question)
                    if args.judge:
                        row["judge"] = await judge(assistant, row)
                    break
                except Exception as error:  # record and continue; --resume retries it later
                    row = {"id": question["id"], "lesson": question["lesson"], "category": question["category"], "question": question["question"], "error": f"{type(error).__name__}: {error}"}
                    if "rate-limited" not in str(error) or attempt == 2:
                        break
                    print(f"[{i}/{len(questions)}] {question['id']} rate-limited, waiting 60s", flush=True)
                    await asyncio.sleep(60)
            results["questions"].append(row)
            write_outputs(out, results)
            status = row.get("error") or (
                f"{row['seconds']}s {row['model']} grounded={row['grounded']} reflectiveQ={row['has_reflective_question']} "
                f"non-directive={row['non_directive']} tool={row['right_tool']} content={row['key_content']}"
                + (f" judge={[row['judge'][k] for k in JUDGE_KEYS]}" if row.get("judge") else "")
            )
            print(f"[{i}/{len(questions)}] {question['id']} {status}", flush=True)
            await asyncio.sleep(args.pause)

        if args.reports:
            done_reports = {r["lesson"]: r for r in results["reports"] if not r.get("error")}
            results["reports"] = []
            for lesson in sorted({q["lesson"] for q in json.loads((EVAL_DIR / "questions.json").read_text(encoding="utf-8"))}):
                if lesson in done_reports:
                    results["reports"].append(done_reports[lesson])
                    continue
                try:
                    row = await check_report(assistant, client, lesson)
                except Exception as error:
                    row = {"lesson": lesson, "error": f"{type(error).__name__}: {error}"}
                results["reports"].append(row)
                write_outputs(out, results)
                print(f"[report] {lesson}: {row.get('error') or str(row['seconds']) + 's grounded=' + str(row['grounded'])}", flush=True)
                await asyncio.sleep(args.pause)
    finally:
        await client.aclose()
        write_outputs(out, results)
    print(f"\nResults in {out}")


if __name__ == "__main__":
    asyncio.run(main())
