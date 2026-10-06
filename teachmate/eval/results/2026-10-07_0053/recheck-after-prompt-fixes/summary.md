# TeachMate evaluation

Run: 2026-10-07 01:06. Models (in fallback order): gemini-3.8-flash, gemini-3.6-flash, gemini-3.5-flash-lite. Questions answered: 4 of 4.

The demo data is synthetic (seeded from the patterns in Chavan & Mitra, 2022). Metrics are automatic heuristics; see Notes.

## Overall

| Metric | Result |
| --- | --- |
| Grounded (every cited number matches its evidence) | 100% (4/4) |
| Mean grounding score | 1.0 |
| Numbers checked in total | 35 |
| Answers repaired by the grounding check | 0% (0/4) |
| Evidence-backed (cites at least one evidence item) | 100% (3/3) |
| Asks the teacher a reflective question | 100% (3/3) |
| Non-directive (no 'you should/must', no yes/no verdict) | 100% (4/4) |
| Used the expected tool | 100% (3/3) |
| Mentions the key content | 100% (4/4) |
| Activity/strategy answers citing the strategy library | n/a |
| Response time: median / max (s) | 4.35 / 6.0 |
| Answered by a fallback model (main model busy) | 100% (4/4) |
| Answers by model | gemini-3.5-flash-lite: 4 |
| AI judge, mean non directive (1-5) | 5 |
| AI judge, mean reflective (1-5) | 4.5 |
| AI judge, mean evidence use (1-5) | 4.75 |
| AI judge, mean usefulness (1-5) | 4.75 |

## By question type

| Type | Questions | Grounded | Reflective question | Non-directive | Expected tool | Key content |
| --- | --- | --- | --- | --- | --- | --- |
| Confusion | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) |
| Off-topic | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | n/a | 100% (1/1) |
| Pressure for a verdict | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) |
| Save a reflection | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) |

## Each question

| ID | Type | Question | Time (s) | Grounded | Reflective Q | Non-directive | Tool | Key content | Judge (ND/R/E/U) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J1 | Confusion | Which concept confused students the most in this lecture? | 6.0 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J6 | Save a reflection | I think I rushed the TestArray demo and the font was too small. Next time I'll zoom in and trace the loop on the board. Can you save that? | 4.6 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J8 | Pressure for a verdict | Just tell me straight: is this a bad lecture? Yes or no. | 4.1 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| X1 | Off-topic | Write me a short poem about microprocessors. | 2.2 | yes (1.0) | yes | yes | n/a | yes | 5/3/4/4 |

## Grounding check on known cases

Correct verdicts on normal cases: 10 of 10 (faulty answers caught: 5 of 5; false alarms: 0).

| Case | Should flag | Flagged | Correct |
| --- | --- | --- | --- |
| Correct number, correct citation | no | no | yes |
| Normal rounding (43.6 -> 44%) | no | no | yes |
| Unicode minus sign | no | no | yes |
| Time range in the sentence | no | no | yes |
| Uncited small number (not a data claim) | no | no | yes |
| Invented percentage | yes | yes | yes |
| Invented count | yes | yes | yes |
| Real number, wrong evidence cited | yes | yes | yes |
| Evidence ID that does not exist | yes | yes | yes |
| Changed number (+9 -> +11) | yes | yes | yes |
| Unit misuse: 17 reasons reported as 17 students (known limitation) | yes | no | **no** |
| Derived duration (6-minute window for min 16-22) (known limitation) | no | yes | **no** |

## Notes

- Reflective question: a sentence ending in '?' addressed to the teacher (contains you/your).
- Non-directive: no 'you should / must / need to / have to' or 'make sure'; for the verdict question, also no flat 'Yes,' or 'No.' at the start.
- Key content: the answer mentions at least one expected element (e.g. the minute or topic the data points to).
- The grounding check verifies numbers against cited evidence. Known limitations (see the cases above): it cannot detect a correct number used with the wrong meaning, and it flags correct numbers the model derived itself (e.g. a window's length).
- The AI judge (if used) is a Gemini model rating TeachMate's own model family; treat its scores as indicative, not independent.
- Free-tier Gemini is often overloaded, so response times and the model that answers vary between runs.
