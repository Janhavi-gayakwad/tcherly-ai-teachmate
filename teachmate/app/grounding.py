"""Grounding check: does every number in an answer come from the evidence it cites?

For each sentence (or bullet) of the answer we collect the numbers it states
and the evidence IDs it cites. A number is *supported* if it appears in one of
the cited evidence items (text or data), allowing for normal rounding and
unicode minus signs. Numbers in sentences without any citation are reported
separately: they may be harmless ("two options", "a 3-column table") but are
worth a look.
"""
import re
from dataclasses import dataclass, field
from typing import Any

from .analytics import EvidenceLog

CITATION = re.compile(r"\[(E\d+(?:\s*,\s*E\d+)*)\]")
NUMBER = re.compile(r"(?<![\w.])[-+−–]?\d+(?:\.\d+)?%?")
LIST_MARKER = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z*\"'(])")


@dataclass
class GroundingReport:
    cited_ids: list[str] = field(default_factory=list)
    unknown_ids: list[str] = field(default_factory=list)
    checked_numbers: int = 0
    unsupported: list[dict[str, Any]] = field(default_factory=list)
    uncited: list[dict[str, Any]] = field(default_factory=list)

    @property
    def grounded(self) -> bool:
        return not self.unknown_ids and not self.unsupported

    @property
    def score(self) -> float:
        """Share of cited-sentence numbers that are supported by their evidence (1.0 = fully grounded)."""
        if not self.checked_numbers:
            return 1.0 if not self.unknown_ids else 0.0
        return round(1 - len(self.unsupported) / self.checked_numbers, 3)

    def as_dict(self) -> dict[str, Any]:
        return {
            "grounded": self.grounded,
            "score": self.score,
            "checked_numbers": self.checked_numbers,
            "cited_ids": self.cited_ids,
            "unknown_ids": self.unknown_ids,
            "unsupported": self.unsupported,
            "uncited": self.uncited,
        }

    def feedback_for_model(self) -> str:
        lines = []
        if self.unknown_ids:
            lines.append(f"- You cited evidence IDs that do not exist: {', '.join(self.unknown_ids)}.")
        for item in self.unsupported:
            lines.append(f"- The number {item['number']} in \"{item['sentence'][:160]}\" is not in the evidence you cited ({', '.join(item['cited'])}).")
        return "\n".join(lines)


def _to_float(token: str) -> float:
    return float(token.replace("%", "").replace("−", "-").replace("–", "-").lstrip("+"))


def _flatten_numbers(value: Any, out: set[float]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.add(abs(float(value)))
    elif isinstance(value, str):
        for token in NUMBER.findall(value):
            out.add(abs(_to_float(token)))
    elif isinstance(value, dict):
        for v in value.values():
            _flatten_numbers(v, out)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _flatten_numbers(v, out)


def _matches(number: float, known: set[float]) -> bool:
    n = abs(number)
    for k in known:
        if abs(n - k) < 1e-9 or round(k) == n or round(k, 1) == n or abs(n - k) <= 0.051:
            return True
    return False


def _sentences(text: str) -> list[str]:
    parts: list[str] = []
    for line in text.splitlines():
        line = LIST_MARKER.sub("", line.strip())
        if not line or line.startswith("#"):
            continue
        parts.extend(s for s in SENTENCE_END.split(line) if s.strip())
    return parts


def check(text: str, evidence: EvidenceLog) -> GroundingReport:
    report = GroundingReport()
    known_by_id: dict[str, set[float]] = {}

    for sentence in _sentences(text):
        cited = [cid for group in CITATION.findall(sentence) for cid in re.split(r"\s*,\s*", group)]
        for cid in cited:
            if cid not in report.cited_ids:
                report.cited_ids.append(cid)
            if evidence.get(cid) is None and cid not in report.unknown_ids:
                report.unknown_ids.append(cid)
        body = CITATION.sub(" ", sentence)
        numbers = [t for t in NUMBER.findall(body)]
        if not numbers:
            continue

        if not cited:
            report.uncited.append({"sentence": sentence, "numbers": numbers})
            continue

        known: set[float] = set()
        for cid in cited:
            item = evidence.get(cid)
            if item is None:
                continue
            if cid not in known_by_id:
                values: set[float] = set()
                _flatten_numbers(item.fact, values)
                _flatten_numbers(item.data, values)
                known_by_id[cid] = values
            known |= known_by_id[cid]

        for token in numbers:
            report.checked_numbers += 1
            if not _matches(_to_float(token), known):
                report.unsupported.append({"number": token, "sentence": sentence, "cited": cited})
    return report
