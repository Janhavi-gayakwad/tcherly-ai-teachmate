# Architecture Diagrams

## System context

```mermaid
flowchart LR
  Teacher[Teacher Browser]
  Student[Student Browser]
  Researcher[Researcher Browser]
  Express[Express server.js]
  Mongo[(MongoDB)]
  YT[YouTube Data API]
  MG[Mailgun]
  YTEmbed[YouTube Embed]

  Teacher --> Express
  Student --> Express
  Researcher --> Express
  Student --> YTEmbed
  Teacher --> YTEmbed
  Express --> Mongo
  Express --> YT
  Express --> MG
```

## Request path (authenticated teacher)

```mermaid
sequenceDiagram
  participant C as React client
  participant A as Auth provider
  participant E as Express /api
  participant P as Passport JWT
  participant Ctrl as Controller
  participant DB as MongoDB

  C->>A: request(GET, url)
  A->>A: Attach Bearer JWT + credentials
  A->>E: HTTP + cookie debe_token
  E->>P: verifyMiddleware
  P->>DB: User.findOne(_id)
  P-->>E: req.user
  E->>Ctrl: handler
  Ctrl->>DB: queries
  DB-->>Ctrl: docs
  Ctrl-->>C: JSON
```

## Feedback analysis pipeline

```mermaid
flowchart TD
  FB[(feedback docs)] --> Group[Group by student_id]
  Group --> Sec[studentSecondArray]
  Sec --> Min[generateStudentMinuteData]
  Min --> Class[generateClassFeedback]
  Class --> MW[generateMovingWindowAnalysis]
  MW --> Net[generateNetDistribution]
  MW --> Pct[generatePercentageFeedback]
  Class --> Click[generateClickDistribution]
  Min --> Over[generateOverlappingData]
  Class --> Venn[generateVennFeedback]
  Venn --> Charts[venn / radial / participation / detailed]
  Net --> LineChart[Line chart series]
  Click --> Gauge[Click distribution]
```

---

# TeachMate (AI reflective teaching assistant)

TeachMate is a separate Python service next to the Node app. It never reads MongoDB's feedback directly: it calls
the Node API with the teacher's own login token, so Tcherly's ownership checks apply to everything the AI sees.

## System context with TeachMate

```mermaid
flowchart LR
  Teacher[Teacher browser<br/>React dashboard + TeachMate drawer]
  Express[Node / Express :3000<br/>analytics pipeline, ownership checks]
  TM[TeachMate FastAPI :8000<br/>tool loop, grounding, reports]
  Gemini[Google Gemini API<br/>chat + embeddings]
  KB[Strategy library<br/>teachmate/knowledge/*.md]
  Mongo[(MongoDB)]

  Teacher -->|dashboard, bookmarks| Express
  Teacher -->|chat, reports, JWT| TM
  TM -->|teacher's JWT: feedback, behaviour, courses, bookmarks| Express
  TM -->|prompts + evidence| Gemini
  TM --> KB
  TM -->|conversations, reports| Mongo
  Express --> Mongo
```

## One chat question

```mermaid
sequenceDiagram
  participant T as Teacher (React)
  participant M as TeachMate
  participant G as Gemini
  participant N as Node API

  T->>M: POST /chat/stream (question, lesson, JWT)
  M->>G: system prompt + question + tool list
  G-->>M: call get_segment_analytics(17, 23)
  M-->>T: status "Looking closely at min 17-23"
  M->>N: GET /lessons/:id/feedback?min=17&max=23
  N-->>M: pipeline output
  M->>M: analytics.py turns it into evidence E1, E2, … (all maths here)
  M->>G: tool results (evidence items)
  G-->>M: answer text citing [E2], [E5] (streamed)
  M-->>T: answer text (streamed)
  M->>M: grounding check: every cited number in its evidence?
  alt a number does not match
    M->>G: "fix only these statements"
    G-->>M: corrected answer
    M-->>T: replace answer
  end
  M-->>T: final answer + evidence + grounding result
```

## Retrieval (RAG) for suggestions

```mermaid
flowchart LR
  P[Problem as students experienced it<br/>e.g. 'too fast, not enough examples in the array demo'] --> E[Embed with gemini-embedding-001]
  Notes[24 strategy notes<br/>cached embeddings] --> R[Rank by similarity]
  E --> R
  Refl[Teacher's reflections<br/>from other lessons] --> S[Semantic similarity >= 0.80<br/>max 2, 'possibly related']
  E --> S
  R --> Ev[Evidence items with source<br/>'Teaching strategy ... Source: ...']
  S --> Ev
  Ev --> G[Gemini builds options to adopt, adapt or reject,<br/>citing each strategy and its source]
```

If the embedding API is unavailable, both rankings fall back to keyword matching.

## Lesson report

```mermaid
flowchart TD
  F[Feedback + viewing logs + bookmarks] --> Sel[report.py picks up to 4 key moments in code<br/>strongest difficult / boring / engaging peaks]
  Sel --> Gat[Gather evidence: overview, each moment, reflections,<br/>viewing behaviour, matching strategies]
  Gat --> J[Gemini writes structured JSON<br/>headline, key moments, what worked, open questions,<br/>options with a required 'based_on' strategy]
  J --> C{Grounding check}
  C -->|ok| Save[(teachmate_reports)]
  C -->|mismatch| Fix[One repair request] --> Save
  Save --> Web[Report page /l/:id/report/:reportId]
  Save --> PDF[Designed A4 PDF, pdfmake in the browser]
```
