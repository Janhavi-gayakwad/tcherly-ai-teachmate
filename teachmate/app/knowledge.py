"""Retrieval (RAG) over TeachMate's teaching-strategy library and the teacher's own past reflections.

The library is the Markdown notes in teachmate/knowledge/ (one strategy per note, each with its source).
Notes are embedded with Gemini's embedding model once and cached in teachmate/.cache/; only new or
changed notes are embedded again. If the embedding service is unavailable (free-tier limits), a keyword
search is used instead, so retrieval always returns something.
"""
import asyncio
import hashlib
import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from google import genai
from google.genai import errors, types

from .config import settings

log = logging.getLogger("teachmate")

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"
CACHE_FILE = ROOT / ".cache" / "knowledge-index.json"
EMBED_MODEL = "gemini-embedding-001"
DIMS = 768
EMBED_TIMEOUT_S = 30

STOPWORDS = set(
    "the and for with that this from are was were but not you your they their them its into than then there these those "
    "have has had can could would should will what when where which who why how all any some more most other such only "
    "also very just about over after before during while because each per one two may might our out off too".split()
)


@dataclass
class Note:
    file: str
    title: str
    summary: str
    helps_with: str
    source: str
    sections: dict[str, str] = field(default_factory=dict)
    raw: str = ""

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.raw.encode("utf-8")).hexdigest()[:16]

    @property
    def search_text(self) -> str:
        return f"{self.title}. {self.summary} Helps with: {self.helps_with}. " + " ".join(self.sections.values())


def parse_note(path: Path) -> Note:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    fields: dict[str, str] = {}
    sections: dict[str, str] = {}
    current, buffer = None, []
    for line in lines[1:]:
        if line.startswith("## "):
            if current:
                sections[current] = " ".join(buffer).strip()
            current, buffer = line[3:].strip(), []
        elif current:
            if line.strip():
                buffer.append(line.strip())
        else:
            match = re.match(r"^(\w+):\s*(.*)$", line)
            if match:
                fields[match.group(1)] = match.group(2).strip()
    if current:
        sections[current] = " ".join(buffer).strip()
    return Note(
        file=path.name,
        title=lines[0].lstrip("#").strip() if lines else path.stem,
        summary=fields.get("summary", ""),
        helps_with=fields.get("helps_with", ""),
        source=fields.get("source", ""),
        sections=sections,
        raw=raw,
    )


def load_notes() -> list[Note]:
    return [parse_note(p) for p in sorted(KNOWLEDGE_DIR.glob("*.md")) if p.name.lower() != "readme.md"]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2 and w not in STOPWORDS]


def keyword_scores(query: str, documents: list[str]) -> list[float]:
    """TF-IDF style overlap; the fallback when embeddings are unavailable."""
    query_terms = set(_tokens(query))
    doc_terms = [_tokens(d) for d in documents]
    df = Counter(term for terms in doc_terms for term in set(terms))
    n = len(documents)
    scores = []
    for terms in doc_terms:
        tf = Counter(terms)
        score = sum((1 + math.log(tf[t])) * math.log((n + 1) / (df[t] + 0.5)) for t in query_terms if t in tf)
        scores.append(score / (1 + math.log(1 + len(terms))))
    return scores


class Library:
    def __init__(self, client: genai.Client | None = None):
        self.client = client or genai.Client(api_key=settings.gemini_api_key)
        self.notes = load_notes()
        self._vectors: dict[str, list[float]] | None = None
        self._lock = asyncio.Lock()

    async def _embed(self, texts: list[str], task: str) -> list[list[float]]:
        response = await asyncio.wait_for(
            self.client.aio.models.embed_content(
                model=EMBED_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task, output_dimensionality=DIMS),
            ),
            timeout=EMBED_TIMEOUT_S,
        )
        return [e.values for e in response.embeddings]

    async def _note_vectors(self) -> dict[str, list[float]]:
        async with self._lock:
            if self._vectors is not None:
                return self._vectors
            cache = {}
            if CACHE_FILE.exists():
                try:
                    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                except ValueError:
                    cache = {}
            if cache.get("model") != EMBED_MODEL or cache.get("dims") != DIMS:
                cache = {}
            stored = cache.get("notes", {})
            missing = [n for n in self.notes if stored.get(n.file, {}).get("digest") != n.digest]
            if missing:
                log.info("embedding %d knowledge note(s)", len(missing))
                vectors = await self._embed([n.search_text for n in missing], "RETRIEVAL_DOCUMENT")
                for note, vector in zip(missing, vectors):
                    stored[note.file] = {"digest": note.digest, "vector": vector}
                CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                current = {n.file: stored[n.file] for n in self.notes}
                CACHE_FILE.write_text(json.dumps({"model": EMBED_MODEL, "dims": DIMS, "notes": current}), encoding="utf-8")
            self._vectors = {n.file: stored[n.file]["vector"] for n in self.notes}
            return self._vectors

    async def search(self, query: str, top_k: int = 3, extra_texts: list[str] | None = None) -> dict:
        """Best matching notes for `query`, plus scores for `extra_texts` (e.g. past reflections).

        Returns {"method": "embeddings"|"keywords", "notes": [(Note, score)], "extra": [score per extra text]}.
        """
        extra_texts = extra_texts or []
        try:
            vectors = await self._note_vectors()
            query_vector = (await self._embed([query], "RETRIEVAL_QUERY"))[0]
            ranked = sorted(((n, cosine(query_vector, vectors[n.file])) for n in self.notes), key=lambda pair: -pair[1])
            extra_scores: list[float] = []
            if extra_texts:
                # Problem-vs-reflection is a like-for-like comparison, which the symmetric
                # SEMANTIC_SIMILARITY mode ranks more reliably than query/document retrieval.
                similar = await self._embed([query] + extra_texts, "SEMANTIC_SIMILARITY")
                extra_scores = [cosine(similar[0], v) for v in similar[1:]]
            return {"method": "embeddings", "notes": ranked[:top_k], "extra": extra_scores}
        except (errors.APIError, TimeoutError, OSError, ValueError, KeyError) as error:
            log.warning("embedding search unavailable (%s); using keyword search", type(error).__name__)
            note_scores = keyword_scores(query, [n.search_text for n in self.notes] + extra_texts)
            ranked = sorted(zip(self.notes, note_scores[: len(self.notes)]), key=lambda pair: -pair[1])
            return {"method": "keywords", "notes": [p for p in ranked[:top_k] if p[1] > 0], "extra": note_scores[len(self.notes):]}


_library: Library | None = None


def library() -> Library:
    global _library
    if _library is None:
        _library = Library()
    return _library
