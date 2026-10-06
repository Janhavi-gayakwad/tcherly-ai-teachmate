"""Test cases for the grounding check: answers with a known correct verdict.

`should_flag` is what a perfect checker would do. Two cases are known limitations:
- unit misuse: the number exists in the evidence, so the checker cannot see that it is used with the wrong meaning;
- derived duration: a correct number the model worked out itself (16-22 is 6 minutes) is not in the evidence, so the
  checker flags it. This false alarm is the price of a strict check; it only costs one repair attempt.

Run from the project folder (no Gemini key needed):
    teachmate/.venv/Scripts/python teachmate/eval/grounding_cases.py     (Windows)
    teachmate/.venv/bin/python teachmate/eval/grounding_cases.py         (macOS/Linux)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # teachmate/, so `app` imports work

from app.analytics import EvidenceLog  # noqa: E402
from app.grounding import check  # noqa: E402


def evidence() -> EvidenceLog:
    log = EvidenceLog()
    log.add(
        "min 16-22: average net difficulty +6.3 (highest +9 in minute 21), average net engagement -1.8 (lowest -6 in minute 21).",
        {"mean_net_difficulty": 6.3},
    )
    log.add("min 16-22: breakdown of the 39 reason selections for 'difficult': Not enough explanation / examples 43.6% (17 of 39), Too fast 28.2% (11 of 39).")
    log.add("min 16-22: 45 of 58 responding students gave feedback in this segment.")
    return log


CASES = [
    # (name, answer, should_flag, limitation)
    ("Correct number, correct citation", "Net difficulty peaked at +9 in minute 21 [E1].", False, False),
    ("Normal rounding (43.6 -> 44%)", "About 44% of the difficult reasons were 'Not enough explanation' [E2].", False, False),
    ("Unicode minus sign", "Engagement fell to −6 in minute 21 [E1].", False, False),
    ("Time range in the sentence", "Between min 16–22, 45 of 58 students responded [E3].", False, False),
    ("Uncited small number (not a data claim)", "You could try 3 short activities in the next class.", False, False),
    ("Invented percentage", "About 60% of students said it was too fast [E2].", True, False),
    ("Invented count", "12 students left the lecture at minute 21 [E1].", True, False),
    ("Real number, wrong evidence cited", "45 students found it difficult [E1].", True, False),
    ("Evidence ID that does not exist", "Students struggled with arrays [E9].", True, False),
    ("Changed number (+9 -> +11)", "Net difficulty peaked at +11 in minute 21 [E1].", True, False),
    ("Unit misuse: 17 reasons reported as 17 students", "17 students said there was not enough explanation [E2].", True, True),
    ("Derived duration (6-minute window for min 16-22)", "Over this 6-minute window (min 16–22), 45 of 58 students responded [E3].", False, True),
]


def run() -> list[dict]:
    rows = []
    for name, answer, should_flag, limitation in CASES:
        report = check(answer, evidence())
        flagged = not report.grounded
        rows.append({"case": name, "should_flag": should_flag, "flagged": flagged, "correct": flagged == should_flag, "known_limitation": limitation})
    return rows


if __name__ == "__main__":
    for row in run():
        print(f"{'OK ' if row['correct'] else 'MISS'} {row['case']}: flagged={row['flagged']} (should be {row['should_flag']})")
