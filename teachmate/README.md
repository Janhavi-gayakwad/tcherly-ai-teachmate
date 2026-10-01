# TeachMate: AI reflective teaching assistant for Tcherly

A FastAPI service that lets a teacher talk with Gemini about their class's DEBE feedback.
The assistant follows Schön's reflective-practice model: it grounds every claim in numbered
evidence from the Tcherly analytics (`[E3]`), offers interpretations rather than verdicts, asks
reflective questions, and frames suggestions as options to adopt, adapt or reject.

## How it works
```
React dashboard -> POST /chat (teacher's Tcherly JWT) -> TeachMate (FastAPI)
                                                          |- Gemini (function calling, model fallback)
                                                          |- tools -> Node API /api/lessons/:id/feedback (ownership-checked)
```
- `app/analytics.py`: turns Tcherly's pipeline output into numbered evidence items (no LLM maths)
- `app/tools.py`: the 5 tools Gemini can call (overview, segment, moments, compare lessons, reflections)
- `app/assistant.py`: tool loop, 45 s timeout per call, fallback to the next model on 429/5xx/timeout
- `app/prompts/system.md`: the reflective-practice system prompt

## Setup
Needs the Node app on :3000 and `GEMINI_API_KEY` in the repo-root `.env`.
```bash
python -m venv teachmate/.venv
teachmate/.venv/Scripts/python -m pip install -r teachmate/requirements.txt
```
Optional `.env` settings: `GEMINI_MODEL` (default `gemini-3.8-flash`), `GEMINI_FALLBACK_MODELS`
(default `gemini-3.6-flash,gemini-3.5-flash-lite`), `TEACHMATE_MODEL_TIMEOUT_S`, `TEACHMATE_CORS_ORIGINS`.

## Run
```bash
# API on http://localhost:8000 (docs at /docs)
teachmate/.venv/Scripts/python -m uvicorn app.main:app --app-dir teachmate --port 8000

# Terminal chat (uses the seeded demo teacher by default)
cd teachmate && .venv/Scripts/python cli.py --evidence "Why did engagement drop?"
```
