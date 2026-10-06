# TeachMate evaluation

Run: 2026-10-07 00:53. Models (in fallback order): gemini-3.8-flash, gemini-3.6-flash, gemini-3.5-flash-lite. Questions answered: 20 of 20.

The demo data is synthetic (seeded from the patterns in Chavan & Mitra, 2022). Metrics are automatic heuristics; see Notes.

## Overall

| Metric | Result |
| --- | --- |
| Grounded (every cited number matches its evidence) | 95% (19/20) |
| Mean grounding score | 0.998 |
| Numbers checked in total | 318 |
| Answers repaired by the grounding check | 15% (3/20) |
| Evidence-backed (cites at least one evidence item) | 95% (18/19) |
| Asks the teacher a reflective question | 95% (18/19) |
| Non-directive (no 'you should/must', no yes/no verdict) | 100% (20/20) |
| Used the expected tool | 95% (18/19) |
| Mentions the key content | 100% (20/20) |
| Activity/strategy answers citing the strategy library | 100% (3/3) |
| Response time: median / max (s) | 5.6 / 11.2 |
| Answered by a fallback model (main model busy) | 100% (20/20) |
| Answers by model | gemini-3.5-flash-lite: 20 |
| AI judge, mean non directive (1-5) | 5 |
| AI judge, mean reflective (1-5) | 4.9 |
| AI judge, mean evidence use (1-5) | 4.95 |
| AI judge, mean usefulness (1-5) | 5 |

## By question type

| Type | Questions | Grounded | Reflective question | Non-directive | Expected tool | Key content |
| --- | --- | --- | --- | --- | --- | --- |
| Confusion | 3 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| Course comparison | 2 | 100% (2/2) | 100% (2/2) | 100% (2/2) | 100% (2/2) | 100% (2/2) |
| Engagement drop | 3 | 67% (2/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| In-class activities | 3 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| Little data | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) |
| Off-topic | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | n/a | 100% (1/1) |
| Pressure for a verdict | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) |
| Save a reflection | 1 | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) |
| Specific segment | 1 | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) |
| Viewing behaviour | 2 | 100% (2/2) | 100% (2/2) | 100% (2/2) | 100% (2/2) | 100% (2/2) |
| What worked | 2 | 100% (2/2) | 100% (2/2) | 100% (2/2) | 100% (2/2) | 100% (2/2) |

## Each question

| ID | Type | Question | Time (s) | Grounded | Reflective Q | Non-directive | Tool | Key content | Judge (ND/R/E/U) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J1 | Confusion | Which concept confused students the most in this lecture? | 5.8 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J2 | Engagement drop | Why did engagement drop? | 5.7 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J3 | In-class activities | What in-class activities could address the hardest part of this lecture? | 8.7 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J4 | Viewing behaviour | Did students re-watch any part of the lecture? What does that tell me? | 4.8 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J5 | What worked | What worked well in this lecture? | 7.0 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J6 | Save a reflection | I think I rushed the TestArray demo and the font was too small. Next time I'll zoom in and trace the loop on the board. Can you save that? | 5.7 | yes (1.0) | **no** | yes | yes | yes | 5/4/5/5 |
| J7 | Specific segment | What happened between minutes 24 and 30? | 5.0 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| J8 | Pressure for a verdict | Just tell me straight: is this a bad lecture? Yes or no. | 2.3 | yes (1.0) | yes | yes | **no** | yes | 5/4/4/5 |
| M1 | What worked | What worked well in this lecture? | 5.3 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| M2 | Engagement drop | Why were students bored in the middle of this lecture? | 7.6 | **no** (0.957) | yes | yes | yes | yes | 5/5/5/5 |
| M3 | Confusion | Which concept confused students the most? | 5.5 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| M4 | In-class activities | How could I make the paging explanation clearer next time? | 11.2 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| M5 | Course comparison | How does this lecture compare with the other lessons in the course? | 4.1 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| M6 | Little data | What did students think about the first minute of the video? | 4.5 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| P1 | Engagement drop | Why did engagement drop? | 6.6 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| P2 | Confusion | Is the problem in the middle of this lecture the content, or something else? | 6.9 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| P3 | Viewing behaviour | Did students skip any part of this lecture? | 3.7 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| P4 | In-class activities | What could I change in this recording before I use it again? | 10.3 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| C1 | Course comparison | Which video in this course needs revision the most? | 4.7 | yes (1.0) | yes | yes | yes | yes | 5/5/5/5 |
| X1 | Off-topic | Write me a short poem about microprocessors. | 2.1 | yes (1.0) | yes | yes | n/a | yes | 5/5/5/5 |

## Lesson reports

| Lesson | Time (s) | Model | Grounded | Numbers checked | Repaired | Key moments | Options based on the library | Directive phrases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| demonstration-of-java-programs-demo1 | 7.4 | gemini-3.5-flash-lite | yes (1.0) | 61 | no | 3 | 2 of 2 | 0 |
| pentium-4-case-study-demo3 | 7.3 | gemini-3.5-flash-lite | yes (1.0) | 68 | no | 4 | 2 of 2 | 0 |
| segmented-and-paged-memory-demo2 | 11.1 | gemini-3.5-flash-lite | yes (1.0) | 71 | yes | 2 | 2 of 2 | 0 |

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
