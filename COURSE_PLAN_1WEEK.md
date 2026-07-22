# One-week plan — 180 students, 2 × 3h sessions + one overnight

**This document supersedes the multi-week timeline in the original
blueprint.** It reflects three simplifying decisions that make N=180 in
one week feasible:

1. **The agent reads the purchase history itself.** No data-export
   requests, no scrapers, no cleaning pipeline, no T−14 lead time. The
   agent's mandatory Bootstrap step (SOUL.md) is: open Your Orders in the
   already-logged-in browser, review ~12 months (capped effort), and write
   `purchase_profile.md` — which then serves as revealed-preference ground
   truth AND as deliverable #2. Students watch their agent learn who they
   are, which is the best three minutes of the course. The old extraction
   scripts remain in `data-pipeline/` as an optional post-course research
   add-on for consenting students (the official Privacy-Central CSV is
   more precise than agent reading, and can be collected after the week).
2. **Infrastructure = GitHub Codespaces on free personal accounts.**
   Every free GitHub account includes 120 core-hours/month (60 h runtime
   on the 2-core machine our devcontainer requests) — no Student Pack, no
   Classroom, no verification wait, no hypervisors, no two-architecture
   images, identical environment for all 180, launched from a browser
   link on any laptop. The lab consumes ~8–10 h. Local VMs are demoted to
   a niche fallback; delete the funnel from the syllabus.
3. **The browsing-history toggle is dropped as a requirement.** You are
   right that it can't be verified at scale and its effect is uncertain.
   Contamination control now rests on the two enforceable layers: the
   agent's search-only candidate rule (in SOUL.md, auditable from the
   decision log) and the automatically computed contamination index (in
   every manifest, usable as a covariate). The toggle survives only as an
   optional note.

## Instructor prep (before the week — this is where the time went)

- [ ] Author the 100 items; build the Form (`build_form.gs`); test-submit.
- [ ] Push this repo as a **template repo** (Settings → Template repository;
      `.devcontainer/` is already at the root); create one codespace yourself and run the FULL lab
      end-to-end including a real amazon.in session. This dry run is the
      only reliable test of CAPTCHA friction from Azure IPs — if it is
      intolerable, the fallback is the instructor-hosted VM fleet, decided
      now, not on day 3.
- [ ] Claude Console: one workspace, hard cap, 180 keys generated via the
      Admin API (a loop, not 180 clicks); distribute key + `DT2026-###`
      pseudonym per student through the LMS.
- [ ] Ethics/consent sheet live in the LMS (research participation
      separable from course requirement; synthetic-persona opt-out ready).
- [ ] TA briefing: with 180 students expect ~10–15 stuck environments in
      session 1 and ~10 CAPTCHally-challenged accounts in session 2. Two
      TAs circulating is the difference between smooth and chaos.

## Session 1 (3h) — environment + identity

| Time | Activity |
|---|---|
| 0:00–0:30 | Lecture: digital twins, agentic commerce, what the experiment tests. Consent walkthrough. |
| 0:30–0:50 | Everyone: create/log into GitHub account → open template repo → **Create codespace**. First build ~4–6 min; the room does the next step while waiting. |
| 0:50–1:10 | Paste Claude API key at `dtlab-start` first-run prompt. Open the Lab Desktop (forwarded port). Smoke test: agent completes the books.toscrape.com sandbox task. Green screenshot = checkpoint 1. |
| 1:10–1:40 | Fill `tasks.md` gift fields; discuss the three task frames; Q&A on what the agent will and won't do (SOUL walk-through — this IS the syllabus content, not admin). |
| 1:40–2:40 | Buffer + triage: TAs fix stragglers; finished students start the questionnaire early. |
| 2:40–3:00 | Assign overnight: complete the Form (~25 min) tonight; **stop your codespace** (core-hours discipline). |
| Overnight | Students: Form. Instructor: export responses → `make_all_personas.py --zip` → post per-student persona zips to the LMS → chase the missing via the roster output. |

## Session 2 (3h) — shop, run, compare (two counterbalanced arms)

Students are pre-randomized (stratified, on the LMS list) into H_FIRST
(human shops, then agent) and A_FIRST (agent first, human shops after,
BLINDED). A_FIRST students sit in pairs and babysit each other's agent
runs; see PERSONALIZATION_PROTOCOL.md Layer 4. Both arms fit the same
3 hours because the two phases mirror each other:

| Time | H_FIRST half | A_FIRST half |
|---|---|---|
| 0:00–0:10 | Persona in, pre-flight, **pause Browsing History (1 day)**, amazon login | same |
| 0:10–0:55 | `dtlab-shop` (own shopping) + pick confirmation | start agent → **swap seats with partner** → babysit partner's run; partner screenshots + empties YOUR cart |
| 0:55–1:05 | break / decay gap | swap back; owners still blind to own results |
| 1:05–1:50 | agent run (watching allowed — your picks are committed) | `dtlab-shop` (own shopping, blinded) + pick confirmation |
| 1:50–2:00 | cart screenshot, empty, skim logs | NOW open your agent's decision log + cart screenshot |
| 2:00–2:40 | `comparison.md` (both arms) | same |
| 2:40–2:55 | `dtlab-pack` + upload (arm auto-recorded in manifest) | same |
| 2:55–3:00 | live verdict poll, split by arm on the slide | same |

## Session 2 (original single-arm version, superseded)

| Time | Activity |
|---|---|
| 0:00–0:10 | Restart codespace; download own persona zip from LMS into `~/dtlab/workspace/`. Pre-flight (`dtlab-start`) goes green or a TA appears. |
| 0:10–0:45 | **`dtlab-shop`** — the student's own logged shopping for the three tasks, incl. amazon.in login (OTP phones out). Ends with pick confirmation → `human_picks.csv`. |
| 0:45–0:55 | Break — doubles as the human→agent decay gap. Cart emptied. |
| 0:55–1:40 | **Agent run**: `dtlab-record`, `dtlab-start`, `/browser connect`, paste the standard prompt. Agent bootstraps (reads Your Orders → writes `purchase_profile.md`) then executes the three tasks. Students watch; intervene only for CAPTCHAs. |
| 1:40–1:50 | Cart screenshot → empty cart → skim `purchase_profile.md` + `decision_log.md`. |
| 1:50–2:35 | Fill `comparison.md`: per task the verdict (better / identical / equivalent / inferior) + attribution and mechanism paragraphs. This is quiet, individual writing time. |
| 2:35–2:50 | `dtlab-pack` → upload zip to LMS. Validation errors → fix → re-pack (2 min loop). |
| 2:50–3:00 | Live poll of verdict distribution across the room (LMS quiz or show of hands per task) — instant cohort result, instant discussion hook for the debrief. |

Remaining 9 classroom hours of the week: lecture content, the cohort-level
results debrief (the day after session 2 — assemble overnight with the
concatenation scripts), and whatever else the course covers.

## What can go wrong at N=180, and the pre-decided answer

| Risk | Answer |
|---|---|
| A student's codespace won't build | Delete + recreate (fresh container). Second failure → pair up for today; the evidence pack is per-ID, sharing a machine sequentially is acceptable in extremis. |
| amazon.in blocks/locks an account from a datacenter IP | Student switches to phone hotspot browsing for the human session and pairs with a neighbor's machine for the agent run — or takes the synthetic-persona path for today. Do NOT burn class time fighting Amazon. |
| A student has no/near-empty Amazon order history | Agent bootstrap writes a thin profile and says so — which is itself analyzable (the persona-only twin). Flag these IDs; they are a natural comparison subgroup, not failures. |
| Wi-Fi collapse with 180 simultaneous sessions | Coordinate with facilities BEFORE the week; codespaces are light (it's a remote desktop stream) but 180 video-ish streams need real AP capacity. Stagger the two daily cohorts (2×90) if the room's network is weak. |
| Claude API rate limits with 180 concurrent agents | One workspace, 180 keys: check the workspace rate-limit tier beforehand; if needed split into two workspaces or stagger cohorts. |
| Form submissions missing at 22:00 | The batch script's roster output + one reminder mail. Persona generation takes seconds per student; a 7:00 regeneration for stragglers is fine. |
