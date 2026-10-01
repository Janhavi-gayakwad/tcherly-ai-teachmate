"""Deterministic analytics on top of the Tcherly feedback pipeline.

The LLM never computes numbers itself. Every tool turns the Node API output
into short, numbered *evidence items* ("E1", "E2", ...). The assistant must
cite these IDs, and the grounding check can verify each cited number.

Time convention (same as the dashboard sliders): "min 16-22" means video
time 16:00-22:00, i.e. per-minute buckets 17..22.
"""
from dataclasses import dataclass, field
from typing import Any

STATES = ("difficult", "easy", "boring", "engaging")
PAIRS = (
    ("difficult", "engaging"),
    ("difficult", "boring"),
    ("difficult", "easy"),
    ("boring", "engaging"),
    ("boring", "easy"),
    ("engaging", "easy"),
)
SIGNALS = {
    "difficulty": ("net_difficult", "net difficulty (difficult minus easy)"),
    "engagement": ("net_engagement", "net engagement (engaging minus boring)"),
}


@dataclass
class Evidence:
    id: str
    fact: str
    data: dict[str, Any]
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "fact": self.fact, "data": self.data}


@dataclass
class EvidenceLog:
    """Collects every evidence item produced during one conversation."""

    items: list[Evidence] = field(default_factory=list)

    def add(self, fact: str, data: dict[str, Any] | None = None, source: str = "") -> Evidence:
        item = Evidence(id=f"E{len(self.items) + 1}", fact=fact, data=data or {}, source=source)
        self.items.append(item)
        return item

    def get(self, evidence_id: str) -> Evidence | None:
        return next((e for e in self.items if e.id == evidence_id), None)


def pct(part: float, whole: float) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def minute_series(feedback: dict) -> list[dict]:
    """Full-lecture per-minute series as drawn on the dashboard line chart (2-minute smoothing)."""
    return [
        {
            "minute": m["minute"],
            "net_difficult": m.get("net_difficult", 0),
            "net_engagement": m.get("net_engagement", 0),
            **{s: m.get(s, 0) for s in STATES},
        }
        for m in feedback.get("minute", [])
    ]


def window_label(start_min: int, end_min: int) -> str:
    return f"min {start_min}-{end_min}"


def find_moments(series: list[dict], signal: str, direction: str, top_k: int = 3) -> list[dict]:
    """Peaks (direction='high') or troughs ('low') of a net signal, expanded into windows."""
    key, _ = SIGNALS[signal]
    sign = 1 if direction == "high" else -1
    values = [sign * m[key] for m in series]
    chosen: list[dict] = []

    for i in sorted(range(len(values)), key=lambda i: values[i], reverse=True):
        peak = values[i]
        # Stop at non-positive values, and ignore blips far smaller than the strongest moment.
        if peak <= 0 or len(chosen) >= top_k or (chosen and peak < 0.4 * chosen[0]["_peak"]):
            break
        if any(abs(i - c["_index"]) <= 2 for c in chosen):
            continue
        threshold = max(1, 0.5 * peak)
        left = i
        while left > 0 and values[left - 1] >= threshold:
            left -= 1
        right = i
        while right < len(values) - 1 and values[right + 1] >= threshold:
            right += 1
        chosen.append(
            {
                "_index": i,
                "_peak": peak,
                "window": window_label(series[left]["minute"] - 1, series[right]["minute"]),
                "start_min": series[left]["minute"] - 1,
                "end_min": series[right]["minute"],
                "peak_minute": series[i]["minute"],
                "peak_value": series[i][key],
            }
        )
    for c in chosen:
        del c["_index"], c["_peak"]
    return chosen


def largest_change(series: list[dict], key: str, span: int = 4, falling: bool = True) -> dict | None:
    """Largest drop (or rise) of a net signal within `span` minutes."""
    best = None
    for i in range(len(series)):
        for j in range(i + 1, min(len(series), i + span + 1)):
            delta = series[j][key] - series[i][key]
            if (falling and delta < 0 and (best is None or delta < best["change"])) or (
                not falling and delta > 0 and (best is None or delta > best["change"])
            ):
                best = {
                    "from_minute": series[i]["minute"],
                    "to_minute": series[j]["minute"],
                    "from_value": series[i][key],
                    "to_value": series[j][key],
                    "change": delta,
                }
    return best


# ---------------------------------------------------------------------------
# Evidence builders (one per tool)
# ---------------------------------------------------------------------------
def lesson_overview(log: EvidenceLog, lesson: dict, feedback: dict) -> list[Evidence]:
    watched = len(lesson.get("watched") or [])
    responders = feedback.get("students_count", 0)
    unique = feedback.get("unique", {})
    series = minute_series(feedback)
    out = [
        log.add(
            f"'{lesson['name']}' is {lesson.get('minutes')} min long; {responders} of {watched} students who opened it "
            f"gave feedback ({pct(responders, watched)}%).",
            {"lesson": lesson["name"], "minutes": lesson.get("minutes"), "watched": watched, "responders": responders},
            "overview",
        ),
        log.add(
            "Students reporting each state at least once in the whole lecture: "
            + ", ".join(f"{s} {unique.get(s, 0)} ({pct(unique.get(s, 0), responders)}%)" for s in STATES)
            + ".",
            {s: unique.get(s, 0) for s in STATES} | {"responders": responders},
            "overview",
        ),
        log.add(
            "Per-minute net values shown on the dashboard line chart (minute: net difficulty / net engagement): "
            + " ".join(f"{m['minute']}:{m['net_difficult']:+d}/{m['net_engagement']:+d}" for m in series),
            {"series": [[m["minute"], m["net_difficult"], m["net_engagement"]] for m in series]},
            "overview",
        ),
    ]

    for signal, direction, label in (
        ("difficulty", "high", "Most difficult moments"),
        ("difficulty", "low", "Easiest moments"),
        ("engagement", "high", "Most engaging moments"),
        ("engagement", "low", "Most boring moments"),
    ):
        moments = find_moments(series, signal, direction, top_k=2)
        if moments:
            out.append(
                log.add(
                    f"{label} ({SIGNALS[signal][1]}): "
                    + "; ".join(f"{m['window']} peaking at {m['peak_value']:+d} in minute {m['peak_minute']}" for m in moments),
                    {"signal": signal, "direction": direction, "moments": moments},
                    "overview",
                )
            )

    drop = largest_change(series, "net_engagement", falling=True)
    if drop:
        out.append(
            log.add(
                f"Largest engagement drop: net engagement fell from {drop['from_value']:+d} (minute {drop['from_minute']}) "
                f"to {drop['to_value']:+d} (minute {drop['to_minute']}), a change of {drop['change']:+d}.",
                drop,
                "overview",
            )
        )
    return out


def segment_analytics(log: EvidenceLog, lesson: dict, feedback: dict, start_min: int, end_min: int, labels: dict) -> list[Evidence]:
    window = window_label(start_min, end_min)
    unique = feedback.get("unique", {})
    in_range = unique.get("users", 0)
    total = feedback.get("students_count", 0)
    out = [
        log.add(
            f"{window}: {in_range} of {total} responding students gave feedback in this segment. Share of them reporting each state: "
            + ", ".join(f"{s} {unique.get(s, 0)} ({pct(unique.get(s, 0), in_range)}%)" for s in STATES)
            + ".",
            {"window": window, "responders_in_segment": in_range, "responders_total": total} | {s: unique.get(s, 0) for s in STATES},
            "segment",
        )
    ]

    overlaps = {f"{a}+{b}": unique.get(f"{a}_{b}", unique.get(f"{b}_{a}", 0)) for a, b in PAIRS}
    out.append(
        log.add(
            f"{window}: students who reported BOTH states in this segment (Venn overlaps): "
            + ", ".join(f"{k} {v}" for k, v in overlaps.items())
            + ".",
            {"window": window, "overlaps": overlaps},
            "segment",
        )
    )

    series = [m for m in minute_series(feedback) if start_min < m["minute"] <= end_min]
    if series:
        mean_d = round(sum(m["net_difficult"] for m in series) / len(series), 1)
        mean_e = round(sum(m["net_engagement"] for m in series) / len(series), 1)
        hi_d = max(series, key=lambda m: m["net_difficult"])
        lo_e = min(series, key=lambda m: m["net_engagement"])
        hi_e = max(series, key=lambda m: m["net_engagement"])
        out.append(
            log.add(
                f"{window}: average net difficulty {mean_d:+.1f} (highest {hi_d['net_difficult']:+d} in minute {hi_d['minute']}), "
                f"average net engagement {mean_e:+.1f} (lowest {lo_e['net_engagement']:+d} in minute {lo_e['minute']}, "
                f"highest {hi_e['net_engagement']:+d} in minute {hi_e['minute']}).",
                {"window": window, "mean_net_difficulty": mean_d, "mean_net_engagement": mean_e,
                 "max_net_difficulty": [hi_d["minute"], hi_d["net_difficult"]],
                 "min_net_engagement": [lo_e["minute"], lo_e["net_engagement"]],
                 "max_net_engagement": [hi_e["minute"], hi_e["net_engagement"]]},
                "segment",
            )
        )

    detailed = feedback.get("detailed", {})
    for state in STATES:
        rows = [r for r in detailed.get(state, []) if not r.get("others") and r.get("key")]
        misc = next((r for r in detailed.get(state, []) if r.get("others")), None)
        free_text = [t for t in (detailed.get("others", {}).get(state) or []) if t]
        if not rows and not free_text:
            continue
        total_reasons = sum(r["value"] for r in rows) + sum(v["value"] for v in (misc or {}).get("values", []))
        parts = [
            f"{labels.get(state, {}).get(r['key'], 'no reason given' if r['key'] == 'none' else r['key'])} "
            f"{round(r['percentage'], 1)}% ({r['value']} of {total_reasons})"
            for r in rows
        ]
        if misc and misc.get("percentage"):
            misc_count = sum(v["value"] for v in misc.get("values", []))
            parts.append(f"other listed reasons {round(misc['percentage'], 1)}% ({misc_count} of {total_reasons})")
        # Percentages are shares of reason selections (one per student per minute), not of students.
        fact = f"{window}: breakdown of the {total_reasons} reason selections for '{state}' (shares of selections, not of students): " + ", ".join(parts)
        counts: dict[str, int] = {}
        for t in free_text:
            counts[t] = counts.get(t, 0) + 1
        if counts:
            fact += "; students' own words: " + "; ".join(f"\"{t}\" x{n}" for t, n in sorted(counts.items(), key=lambda kv: -kv[1])[:6])
        out.append(log.add(fact + ".", {"window": window, "state": state, "reasons": rows, "free_text": counts}, "segment"))
    return out


def moments(log: EvidenceLog, feedback: dict, signal: str, direction: str, top_k: int) -> list[Evidence]:
    found = find_moments(minute_series(feedback), signal, direction, top_k)
    word = {"difficulty": ("difficult", "easy"), "engagement": ("engaging", "boring")}[signal][0 if direction == "high" else 1]
    if not found:
        return [log.add(f"No clearly {word} moments were found (the {SIGNALS[signal][1]} never moves in that direction).", {}, "moments")]
    return [
        log.add(
            f"Most {word} moments by {SIGNALS[signal][1]}: "
            + "; ".join(f"{m['window']} (peak {m['peak_value']:+d} at minute {m['peak_minute']})" for m in found),
            {"signal": signal, "direction": direction, "moments": found},
            "moments",
        )
    ]


def lesson_summary_row(lesson: dict, feedback: dict) -> dict:
    series = minute_series(feedback)
    n = len(series) or 1
    watched = len(lesson.get("watched") or [])
    struggling = sum(1 for m in series if m["net_difficult"] > 0 and m["net_engagement"] < 0)
    worst = min(series, key=lambda m: m["net_engagement"]) if series else None
    hardest = max(series, key=lambda m: m["net_difficult"]) if series else None
    return {
        "lesson": lesson["name"],
        "lesson_id": lesson.get("id"),
        "minutes": lesson.get("minutes"),
        "watched": watched,
        "responders": feedback.get("students_count", 0),
        "participation_pct": pct(feedback.get("students_count", 0), watched),
        "mean_net_difficulty": round(sum(m["net_difficult"] for m in series) / n, 1),
        "mean_net_engagement": round(sum(m["net_engagement"] for m in series) / n, 1),
        "struggle_minutes": struggling,
        "struggle_minutes_pct": pct(struggling, n),
        "peak_difficulty": {"minute": hardest["minute"], "value": hardest["net_difficult"]} if hardest else None,
        "lowest_engagement": {"minute": worst["minute"], "value": worst["net_engagement"]} if worst else None,
    }


def compare_lessons(log: EvidenceLog, course_name: str, rows: list[dict]) -> list[Evidence]:
    ranked = sorted(rows, key=lambda r: (-r["struggle_minutes_pct"], r["mean_net_engagement"]))
    return [
        log.add(
            f"Lessons in '{course_name}', sorted by share of 'struggle minutes' (minutes where net difficulty > 0 while net engagement < 0; "
            "one heuristic among several, so weigh the other columns too): "
            + "; ".join(
                f"{r['lesson']} ({r['minutes']} min): {r['struggle_minutes']} struggle minutes ({r['struggle_minutes_pct']}%), "
                f"avg net difficulty {r['mean_net_difficulty']:+.1f} (peak {r['peak_difficulty']['value']:+d} at minute {r['peak_difficulty']['minute']}), "
                f"avg net engagement {r['mean_net_engagement']:+.1f} (lowest {r['lowest_engagement']['value']:+d} at minute {r['lowest_engagement']['minute']}), "
                f"participation {r['participation_pct']}%"
                for r in ranked
            ),
            {"course": course_name, "lessons": ranked},
            "compare",
        )
    ]


def reflections(log: EvidenceLog, lesson: dict) -> list[Evidence]:
    bookmarks = [b for b in lesson.get("bookmarks") or [] if isinstance(b, dict)]
    if not bookmarks:
        return [log.add(f"The teacher has no saved bookmarks or reflections for '{lesson['name']}' yet.", {}, "reflections")]
    out = []
    for b in bookmarks:
        questions = [q.get("name") for q in b.get("questions", []) if q.get("name")]
        actions = [a.get("action") or a.get("future_action") for a in b.get("actions", []) if a.get("action") or a.get("future_action")]
        out.append(
            log.add(
                f"Saved bookmark '{b.get('topic')}' ({window_label(b.get('time_from', 0), b.get('time_to', 0))}); "
                f"teacher's questions: {questions or 'none'}; actions noted: {actions or 'none'}.",
                {"topic": b.get("topic"), "time_from": b.get("time_from"), "time_to": b.get("time_to"), "questions": questions, "actions": actions},
                "reflections",
            )
        )
    return out
