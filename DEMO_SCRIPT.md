# TeachMate demo script

A walkthrough of about 12 minutes for the final presentation, plus a checklist and a backup plan. It follows the five
parts the group already presents. New features are added to the member whose part they extend.

| Member | Part | New in the final phase |
| --- | --- | --- |
| 1 | Tcherly base platform and setup | Viewing behaviour from the player logs (Node endpoint `/api/lessons/:id/behaviour`) |
| 2 | Demo data and security | Re-watch/skip patterns in the seed; owner check on the new endpoints; one login per device (sessions fix) |
| 3 | TeachMate backend | Report generator (`report.py`), strategy library and embeddings (`knowledge.py`) |
| 4 | AI behaviour and grounding | Strategy rules in the prompt (name and credit the source), evaluation (`teachmate/eval/`) |
| 5 | Frontend and live demo | Reports tab, report page and the designed PDF |

---

## Before the presentation

**The day before**
- [ ] `npm run dev` on the presenting laptop, and check that all three parts start (`[api]`, `[web]`, `[ai]`).
- [ ] Ask TeachMate one question and generate one report, to check the key and the quota.
- [ ] Don't run the evaluation on the demo laptop on the demo day: it uses a large share of the free daily limit.

**30 minutes before**
1. Start MongoDB, then `npm run seed` (resets the demo data and removes old chats and reports).
2. `npm run dev`, and wait for the `[ai]` line `Uvicorn running on http://127.0.0.1:8000` and for the website to open.
3. Log in at http://localhost:8080 as `demo.teacher@tcherly.local` / `Demo@1234`.
4. Open the Java lesson dashboard: http://localhost:8080/l/demonstration-of-java-programs-demo1/dashboard
5. **Warm-up** (so the live answers are fast): ask *"What in-class activities could address the hardest part?"* once. This prepares the strategy library. Then click the **+** (New conversation) button.
6. Generate one **Lesson report** and keep it open in a second tab, as a fallback.
7. Close other tabs and notifications. Zoom the browser to 110–125% so the room can read it.

---

## The walkthrough

### 1. The problem (Member 1, about 1.5 min)
- Show the student view: a video with **Difficult / Easy / Boring / Engaging** buttons (open the lesson in a private window, demo student `student01@demo-student.tcherly.local` / `Student@1234`).
- Back on the teacher dashboard, show the line chart. *"Around minute 20, difficulty (red) peaks and engagement (green) falls. Tcherly shows **what** happened, but working out **why**, and what to do about it, takes time and data skills. That's the gap TeachMate fills."*

### 2. The data behind it (Member 2, about 1 min)
- *"The demo course is synthetic: 90 students and 3 lessons, seeded from the patterns in the Tcherly paper. That way no real student data ever goes to the AI."*
- *"TeachMate reads the data through Tcherly's own API with the teacher's login, so a teacher can only ever see their own lessons. We fixed a security hole where any logged-in teacher could read any lesson."*

### 3. Asking about the class (Member 3, about 2.5 min)
Click **Ask TeachMate**, then the suggested question **"Why did engagement drop?"**
- Point at the status lines (*"Looking closely at min 17-23…"*): *"Gemini decides which analytics tools to call. The numbers come from our code, not from the AI."*
- Click an evidence chip such as **[E4]**: *"Every number is cited and can be checked."*

Then type: **"Did students re-watch any part of the lecture?"**
- Expected: many students jumped back to around **minute 17**, where the difficulty starts. *"This comes from the video player logs. When students rewind to the hard part, that backs up what they clicked."*

### 4. A reflective partner, not a judge (Member 4, about 3 min)
Type: **"Just tell me straight: is this a bad lecture? Yes or no."**
- Expected: it declines the verdict, then shows the strongest and the hardest moments and asks the teacher a question. *"That's Schön's reflective practice: the teacher decides, TeachMate supports their thinking."*

Type: **"What in-class activities could address the hardest part?"**
- Expected: options such as worked examples, code tracing or peer instruction, each **named with its source** (e.g. *Sweller & Cooper*) and offered to *adopt, adapt or reject*. *"These come from a library of 24 research-based strategies that we retrieve with embeddings (RAG). It can also bring back the teacher's own reflection from another lesson."*

*"Is it reliable? We built an evaluation"* (show `teachmate/eval/results/2026-10-07_0053/summary.md`):
*"20 teacher questions: 19 of 20 answers fully grounded across 318 numbers checked, 20 of 20 non-directive, and all 3 reports grounded. It also found real problems. It once wrote a poem when asked, so we added an on-topic rule. Our grounding checker has a known limitation, which we document."*

### 5. Closing the loop: reflection and report (Member 5, about 3 min)
Type: **"I think I rushed the TestArray demo and the font was too small. Next time I'll zoom in and trace the loop on the board. Can you save that?"**
- A **reflection card** appears. Edit a word, then click **Save to bookmarks**. Show it in the dashboard's *Your bookmarks* panel. *"Nothing is saved until the teacher clicks Save."*

Click **Lesson report**, then **Generate a new report** (10–60 s; talk over the status lines). Click **Open report**:
- Walk through the page: headline, key moments, *What worked*, the reflection just saved, *Questions to explore*, *Options to consider* with **Based on**.
- Click **Download PDF** and open it. *"A one-page summary a teacher could bring to a department meeting."*

### Wrap-up (any member, 30 s)
*"Tcherly gave teachers the data. TeachMate turns it into a conversation that ends in a reflection and a plan, without taking the decision away from the teacher."*

---

## If something goes wrong

| Problem | What to do |
| --- | --- |
| *"All Gemini models are busy or rate-limited"* | Wait 30 s and click the question again. If the free daily limit is used up, switch to the backup laptop (another member's key) or show the pre-generated report and the screenshots. |
| An answer takes more than 30 s | Keep talking: explain the status lines and the tool calls. TeachMate switches to a backup model by itself after 45 s. |
| The answer is different from this script | That's normal: the AI's wording changes each time. The facts (minute 17–21, the audio problem in the Pentium lesson) come from the data and stay the same. |
| The page logged out | Log in again. Running `npm run seed` recreates the demo teacher, so log in after seeding. |
| Nothing works | Use the report tab you opened before the presentation, plus screenshots. Take screenshots of each step during the rehearsal. |

## Likely questions from the panel

- **Does the AI make up numbers?** It's told never to, all maths happens in our code, and a grounding check compares each cited number with the evidence and asks for a correction. In the evaluation, 19 of 20 answers passed. The one failure was a correct but derived number ("2-minute window").
- **Why Gemini?** Free tier, function calling, streaming and embeddings, and it doesn't need a GPU. TeachMate falls back across three models when one is busy.
- **What is RAG here?** Retrieval-augmented generation: before suggesting anything, TeachMate searches a library of cited teaching strategies and the teacher's past reflections, and builds its options on what it finds.
- **What about privacy?** Only the synthetic demo data is sent. With real classes, a paid tier (no training on prompts) or a local model would be needed, and students would need to give consent.
- **What would you do next?** A study with real teachers rating the answers, and a local open-source model for privacy.
- **How did you use AI to build it?** See *How this project was built* in the README. Each member should be ready to explain their own part in their own words.
