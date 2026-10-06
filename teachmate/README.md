# TeachMate: AI reflective teaching assistant for Tcherly

A FastAPI service that lets a teacher talk with Gemini about their class's DEBE feedback and generate a short lesson
report. The assistant follows Schön's reflective-practice model: it grounds every claim in numbered evidence from the
Tcherly analytics (`[E3]`), offers interpretations rather than verdicts, asks reflective questions, and frames
suggestions as options to adopt, adapt or reject, built on cited teaching strategies.

## How it works
```
React dashboard ──(teacher's Tcherly JWT)──► TeachMate (FastAPI, :8000)
                                               ├─ Gemini: function calling, streaming, model fallback on 429/5xx/timeout
                                               ├─ tools ──► Node API :3000 (/api/lessons/:id/feedback, /behaviour, /courses …; owner-checked)
                                               ├─ knowledge library (24 cited strategy notes, Gemini embeddings, keyword fallback)
                                               ├─ grounding check: every cited number must be in its evidence, one automatic repair
                                               └─ MongoDB: teachmate_conversations, teachmate_reports
```

| File | What it does |
| --- | --- |
| `app/main.py` | The API: chat (plain and streaming), conversations, reflections, reports |
| `app/assistant.py` | Gemini tool loop, streaming, 45 s timeout per call, fallback to the next model |
| `app/tools.py` | The 8 tools Gemini can call (below) and the per-conversation evidence log |
| `app/analytics.py` | Turns Tcherly's analytics into numbered evidence items. All maths is done here, never by the LLM |
| `app/grounding.py` | Checks every number in a cited sentence against the cited evidence |
| `app/knowledge.py` | RAG: embeds the strategy notes and the teacher's past reflections, ranks them for a problem |
| `app/report.py` | Lesson report: picks the key moments in code, Gemini writes structured JSON, grounding-checked |
| `app/store.py` | MongoDB storage for conversations and reports |
| `app/auth.py` | Verifies the Tcherly JWT (same secret as the Node app) |
| `app/prompts/system.md`, `report.md` | The reflective-practice system prompt and the report instructions |
| `knowledge/*.md` | The teaching-strategy library (format in `knowledge/README.md`) |
| `eval/` | Evaluation: 20 questions, grounding test cases, runner and results (see `eval/README.md`) |
| `cli.py` | Chat with TeachMate from the terminal |

## Tools

| Tool | Gives Gemini |
| --- | --- |
| `get_lesson_overview` | Participation, overall difficulty/engagement, peaks and the biggest changes |
| `get_segment_analytics` | One time window: who responded, states, reasons students gave, their own words |
| `find_moments` | The most difficult, easiest, most boring or most engaging minutes |
| `compare_course_lessons` | The other lessons in the same course, side by side |
| `get_viewing_behaviour` | Where students re-watched, skipped ahead or stopped watching (from the player logs) |
| `get_teacher_reflections` | The teacher's saved bookmarks, questions and actions for this lesson |
| `find_teaching_strategies` | RAG: the best-matching strategy notes (with sources) and possibly related reflections from the teacher's other lessons |
| `propose_reflection` | Drafts a reflection card that the teacher can edit and save as a Tcherly bookmark |

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /chat/stream` | Chat with live status lines and streamed text (used by the website) |
| `POST /chat` | The same, as one JSON response |
| `GET /conversations`, `GET /conversations/{id}` | The teacher's past chats |
| `POST /reflections/draft`, `POST /reflections` | Draft a reflection from a chat; save it as a bookmark |
| `POST /reports`, `GET /reports?lesson_id=`, `GET /reports/{id}` | Generate, list and open lesson reports |
| `GET /health` | Status and the model order |

Interactive docs: http://localhost:8000/docs

## Setup
Needs the Node app on :3000 and `GEMINI_API_KEY` in the repo-root `.env`. `npm run setup` does all of this; manually:
```bash
python -m venv teachmate/.venv
teachmate/.venv/Scripts/python -m pip install -r teachmate/requirements.txt
```
Optional `.env` settings: `GEMINI_MODEL` (default `gemini-3.8-flash`), `GEMINI_FALLBACK_MODELS`
(default `gemini-3.6-flash,gemini-3.5-flash-lite`), `TEACHMATE_MODEL_TIMEOUT_S` (45), `TEACHMATE_REPORT_TIMEOUT_S` (120),
`TEACHMATE_CORS_ORIGINS`.

The strategy notes are embedded once with `gemini-embedding-001` and cached in `teachmate/.cache/` (rebuilt when a
note changes). If embeddings are unavailable, retrieval falls back to keyword matching.

## Run
```bash
# Everything (website, Node server, TeachMate), from the project folder
npm run dev

# TeachMate alone, on http://localhost:8000 (restarts when app/ or prompts/ change)
npm run dev:ai

# Terminal chat (uses the seeded demo teacher by default)
cd teachmate && .venv/Scripts/python cli.py --evidence "Why did engagement drop?"

# Evaluation (about 10-15 minutes; results in teachmate/eval/results/)
teachmate/.venv/Scripts/python teachmate/eval/run_eval.py --judge --reports --pause 20
```
On macOS/Linux use `.venv/bin/python` instead of `.venv/Scripts/python`.

## Adding a teaching strategy
Add a Markdown file to `knowledge/` in the format described in `knowledge/README.md` (title, summary, helps_with,
source, and the sections *When it can help*, *Try it*, *How to tell if it helped*). Restart TeachMate; the note is
embedded on first use.
