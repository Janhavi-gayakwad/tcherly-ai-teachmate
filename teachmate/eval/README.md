# TeachMate evaluation

How we test whether TeachMate behaves the way the project promises: answers grounded in the class data, reflective
(Schön) rather than directive, and useful to a teacher.

## What is in this folder

| File | What it is |
| --- | --- |
| `questions.json` | 20 teacher questions over the 3 demo lessons, each with the tools we expect it to use and key content the answer should mention. They cover confusion, engagement drops, what worked, in-class activities, viewing behaviour, a specific segment, course comparison, saving a reflection, a minute with very little data, pressure for a yes/no verdict, and an off-topic request. |
| `grounding_cases.py` | 12 hand-written answers with a known correct verdict, to test the grounding checker itself (10 normal cases, 2 known limitations). |
| `run_eval.py` | Runs everything and writes the results. |
| `results/<date_time>/` | One folder per run: `summary.md` (tables for the report), `results.csv` (one row per question), `results.json` (everything, including every answer). |

## How to run it

The Node server must be running (`npm run dev`), the demo data seeded (`npm run seed`) and `GEMINI_API_KEY` set in `.env`.
From the project folder:

```
teachmate/.venv/Scripts/python teachmate/eval/run_eval.py --judge --reports     (Windows)
teachmate/.venv/bin/python teachmate/eval/run_eval.py --judge --reports         (macOS/Linux)
```

- `--judge` also asks Gemini to rate each answer 1–5 (non-directive, reflective, evidence use, usefulness).
- `--reports` also generates and checks one lesson report per demo lesson.
- `--only J1,P2` runs only some questions. `--pause 20` waits between questions (free-tier rate limits).
- `--resume <results folder>` continues a run that stopped (e.g. on a rate limit): answered questions are kept, failed ones are retried.

The grounding cases alone (no Gemini needed): `teachmate/.venv/Scripts/python teachmate/eval/grounding_cases.py`
(macOS/Linux: `teachmate/.venv/bin/python …`).

A full run takes about 10–15 minutes. TeachMate is called in-process with the demo teacher's login, through the same
code as the website, so nothing is added to the teacher's chat history or saved reports.

## What is measured

| Metric | How |
| --- | --- |
| Grounded | Every number in a sentence with a citation `[E#]` appears in the cited evidence (the same check that runs live in the app). |
| Evidence-backed | The answer cites at least one evidence item. |
| Reflective question | The answer asks the teacher at least one question (a sentence ending in "?" with "you/your"). |
| Non-directive | No "you should / must / need to / have to", "make sure"; for the verdict question, no flat "Yes," or "No." opening. |
| Expected tool | TeachMate called one of the analytics tools the question needs. |
| Key content | The answer mentions what the data points to (e.g. minute 17 or "TestArray" for the Java confusion question). |
| Strategy library | Answers about activities/changes cite at least one teaching strategy from the knowledge library (RAG). |
| Reports | Grounded, number of key moments, how many options are "based on" a library strategy, directive phrases. |
| AI judge (optional) | Gemini rates each answer 1–5 against TeachMate's intended behaviour. |

## Results (run 2026-10-07, `results/2026-10-07_0053/`)

All 20 answers and 3 reports came from **gemini-3.5-flash-lite**: the two main models had used their free daily quota.

| | Result |
| --- | --- |
| Grounded answers | 19 of 20 (318 numbers checked, mean grounding score 0.998) |
| Evidence-backed | 18 of 19 on-topic answers |
| Asks a reflective question | 18 of 19 on-topic answers |
| Non-directive | 20 of 20 |
| Used the expected tool | 18 of 19 |
| Key content | 20 of 20 |
| Activity answers citing the strategy library | 3 of 3 |
| Median / max response time | 5.6 s / 11.2 s |
| Lesson reports grounded | 3 of 3 (200 numbers checked), 6 of 6 options based on a library strategy, 0 directive phrases |
| Grounding checker on known cases | 10 of 10 correct (5 of 5 faulty answers caught, 0 false alarms) |
| AI judge means (1–5) | non-directive 5.0, reflective 4.9, evidence use 4.95, usefulness 5.0 |

## What the evaluation found, and what we changed

| Found | Cause | Change |
| --- | --- | --- |
| Asked for a poem (X1), the fallback model wrote one. | The system prompt had no rule for off-topic requests. | Added a "Staying on topic" section to `app/prompts/system.md`. Fixed before the main run, where X1 then declined politely. |
| P3 counted as "directive". | Bug in our metric: "Yes, students did skip ahead" is a factual answer, not a verdict. | The yes/no check now applies only to the verdict question. |
| M2 not grounded. | The model wrote "the 2-minute window (min 4–6)". The 2 is correct but derived, so it isn't in the evidence. | None: the checker stays strict (a false alarm costs one repair attempt; a missed wrong number would mislead the teacher). Added as a known-limitation test case. |
| J8 ("is this a bad lecture? yes or no") declined the verdict but didn't look at the data. | Nothing told it what to do instead of a verdict. | Prompt: when asked for a verdict, show the strongest and the most challenging moments so the teacher can judge. |
| J6 (teacher shares a reflection and asks to save it) drafted the card but asked no question. | The model treated "save it" as the whole task. | Prompt: deepen the teacher's reflection with a question, also when offering to save it. |

After the two prompt changes we re-ran J6, J8, J1 and X1 (`results/2026-10-07_0053/recheck-after-prompt-fixes/`):
all four passed every check. J8 now cites the data (peaks at minutes 6–11, difficulty peak at minute 21) before asking
the teacher what happened, and J6 ends with a follow-up question.

## Limitations

- The demo data is synthetic (seeded from the patterns in Chavan & Mitra, 2022), not real classes, and there are only 20 questions.
- The metrics are automatic heuristics. For example, "reflective question" only checks that a question is addressed to the teacher, not that it is a good one.
- The AI judge is a Gemini model rating Gemini answers, so its scores are indicative, not independent. A small study with real teachers rating the answers would be the proper next step.
- Gemini's answers vary between runs, and on the free tier the answering model depends on quota at the time of the run.
- The grounding checker cannot see a correct number used with the wrong meaning (e.g. 17 *reasons* reported as 17 *students*), and it flags correct numbers the model derived itself.
