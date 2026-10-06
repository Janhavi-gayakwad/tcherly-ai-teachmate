# TeachMate knowledge library

These notes are the teaching strategies TeachMate can retrieve (RAG) when it suggests options or in-class activities.
The tool `find_teaching_strategies` searches them together with the teacher's own reflections from their other
lessons, and the AI must cite what it uses.

## Adding or editing a note

Create a `.md` file in this folder with this shape:

```markdown
# Name of the strategy
summary: One sentence saying what it is.
helps_with: The DEBE signals and reasons it fits, e.g. "Too fast"; "Complex terms (jargon)"; students skipping ahead
source: Author, A. (Year). Title. Journal or publisher.

## When it can help
What is known about it, and from which study (keep to what the source actually says).

## Try it
One or two concrete steps a teacher can take.

## How to tell if it helped
What to watch in Tcherly next time (which feedback, reasons or viewing behaviour should change).
```

Rules:

- Cite a real, checkable source. Claim only what that source supports, and avoid precise numbers you can't verify.
- Keep notes short (about 150 words) so the AI can use several at once.
- The search index updates itself: new or changed notes are embedded with Gemini the next time a search runs.
  The cache lives in `teachmate/.cache/` and isn't committed.
