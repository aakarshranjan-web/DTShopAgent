# Lab week plan — 161 students, Sessions 6–10, the 2×2 experiment

**This document is the single authority on the operative plan and the
infrastructure decision** (GitHub Codespaces primary; local VMs per
`provisioning/VM_DISTRIBUTION.md` as fallback).

**Cohort structure:** N=161 in two sections — Section 1 (n=80) meets 3
hours each morning, Section 2 (n=81) 3 hours each afternoon, Monday
through Friday. Both sections run the identical plan, staggered
morning/afternoon — which also caps peak Wi-Fi, Codespaces, and API
concurrency at ~80, never 161.

**Experimental design (plan of record):** the task set is **five
self-purchase categories** picked by the teaching team from the
10-category catalog in `tasks_config.csv` (a provisional five ships
active; no gift, no replenishment framing — every task is buying for
yourself), shopped in a **per-student randomized order** (derived from
the pseudonym, enforced by dtlab-start, identical for the human session
and all agent runs). Every student's picks are
committed on Wednesday; every agent then runs the SAME task set **four
times** in a within-student 2×2 — grounding (persona = questionnaire +
purchase profile vs. ablated = purchase profile only) × model tier
(economy/Haiku-class on Thursday vs. frontier/Sonnet-class on Friday).
Grounding order is counterbalanced within each day (per-day
P_FIRST/NP_FIRST on the LMS list); tier is deliberately confounded with
day and stated as such in the methods. All students are human-first;
**nobody watches their own agent** — self-selected pairs swap seats for
every run (assessment blinding + CAPTCHA handling; see
PERSONALIZATION_PROTOCOL.md Layer 4). Recommended personal spend limit:
**$20** (four runs ≈ $3–6 with retries).

Three standing simplifications carried over from earlier drafts: the
agent reads the purchase history itself at Bootstrap (no extraction
pipeline; `data-pipeline/` is an optional post-course add-on);
infrastructure is Codespaces on the students' free GitHub accounts; the
agent shops the full site with only browsing-history-derived modules
banned and every candidate's provenance logged (PERSONALIZATION_PROTOCOL
Layer 2).

## Pre-week checklist (published end of week 1 · hard deadline Sunday night)

Student homework, LMS checklist with screenshots — never a lab-day
activity:

- [ ] Consent sheet (research participation separable from the course
      requirement; names the partner-pairing disclosure and the ablated
      runs' constraint-blindness; synthetic-persona opt-out available).
- [ ] The 115-item questionnaire (~30 min).
- [ ] Own Anthropic Console account: billing, small credit purchase,
      personal **monthly spend limit ~$20**, one API key.
- [ ] Free GitHub account.

Instructor/TA over the weekend:

- [ ] Export Form responses → `make_all_personas.py --zip` → per-student
      persona zips on the LMS; chase stragglers via the roster output.
- [ ] Publish the assignment sheet: pseudonym + per-day grounding order
      (Thu: P_FIRST/NP_FIRST; Fri: independently re-randomized),
      stratified by section. Publish the pairing instructions
      (self-selected pairs, registered on the sheet).
- [ ] Installer checksums pinned, template repo + Codespaces prebuilds
      live, CI green, dry run complete (docs/CHANGELOG.md T-21 list).

## Session 6 (Mon) — Agentic AI + the build begins

| Time | Activity |
|---|---|
| 0:00–0:30 | Intro to agentic AI (slides). |
| 0:30–1:00 | Reading discussion: "Regulating advanced artificial agents" (Russell et al.). |
| 1:00–1:20 | The capstone project brief + consent walkthrough; every student leaves knowing their pseudonym, pair, and per-day condition order. |
| 1:20–2:30 | **Hermes + SOUL.md**: the agent identity file as the architecture-and-governance lecture material — identity, grounding, ECP logging, hard boundaries, injection hardening. Create codespaces (first build runs while discussing). |
| 2:30–3:00 | Smoke test (sandbox task) = **checkpoint 1**; TAs note failures for overnight triage. |

## Session 7 (Tue) — Components, Architectures, Governance + build complete

| Time | Activity |
|---|---|
| 0:00–1:30 | Lecture: autonomous agents — components, architectures, governance (SOUL.md and the kit's enforcement machinery as the running case). |
| 1:30–2:40 | Hands-on completion: persona files in, pre-flight green (it announces each student's randomized task order), one full sandbox agent run watched end-to-end. **Checkpoint 2 = fully green environment.** |
| 2:40–3:00 | Q&A on what the agent will and won't do; stragglers booked into office hours. |

## Session 8 (Wed) — "When to Specialize" + the human session

| Time | Activity |
|---|---|
| 0:00–1:20 | Lecture + reading discussion: GenAI model portfolios for demand sensing — framed by tomorrow's live question (you run the economy model Thursday; Friday we test whether the frontier model earns its price). |
| 1:20–1:30 | Browsing-history pause (1 day) + payment-methods check. |
| 1:30–2:20 | **`dtlab-shop`** — everyone shops their tasks themselves, ONE AT A TIME in their assigned order (the terminal walks them through; Enter after each cart-add — this is what makes per-task searches/views/time exactly measurable), amazon.in login (OTP phones out), pick confirmation → committed picks. |
| 2:20–3:00 | Problem-resolution buffer: TAs clear every remaining red pre-flight; anyone not green books office hours before Thursday. |

## Session 9 (Thu) — Experiment I: the economy twin (2 runs)

| Time | Activity |
|---|---|
| 0:00–0:15 | Re-pause browsing history (pre-flight gate); pairs seated together; login check. |
| 0:15–1:15 | **Agent run 1** (economy tier; grounding per assigned order) — **swap seats**: partner babysits, handles CAPTCHAs, then runs `dtlab-cart` (automatic cart screenshot + parsed cart contents, cross-checked against the agent's picks at pack time) and empties the cart. |
| 1:15–1:30 | Swap back; break. Owners do NOT open logs yet. |
| 1:30–2:30 | **Agent run 2** (economy tier; other grounding) — same swap protocol; `dtlab-cart`; cart emptied. |
| 2:30–3:00 | Owners open their artifacts for the first time and run **`dtlab-verdict`** — a guided prompt capturing, per task and run: verdict (better/identical/equivalent/inferior), own and agent satisfaction ratings (1–10), and a one-line rationale. Structured capture, no markdown editing. |

## Session 10 (Fri) — Experiment II: will a better model do better? + debrief

| Time | Activity |
|---|---|
| 0:00–0:15 | **Re-pause browsing history** (the 1-day pause has lapsed — pre-flight gates on it); pairs seated. |
| 0:15–1:10 | **Agent run 3** (frontier tier; grounding per Friday's re-randomized order) — swap protocol; `dtlab-cart`. |
| 1:10–2:00 | **Agent run 4** (frontier tier; other grounding) — swap protocol; `dtlab-cart`; cart emptied. |
| 2:00–2:35 | `dtlab-verdict` (frontier rows, head-to-heads, tier question, Overall reflections); `dtlab-pack`; upload the single zip via the BITSoM LMS assignment. |
| 2:35–3:00 | Debrief: hyperpersonalization / agentic demand commitments as the closing frame + live verdict poll from the room. |

**After Friday:** instructor runs `tools/analyze_cohort.py` across both
sections' zips, shares the cohort report with the class (weekend).
Full-class discussion of the report happens through the capstone essay
(and in any spare course slot if available).

## Capstone (individual essay)

Out: when the cohort report is shared · Due: ~1 week after course end ·
3–5 pages. Full text: `docs/SYLLABUS_BLURB.md`. In short: using BOTH
your own evidence pack and the cohort report, analyze the findings
(what the questionnaire added, what the frontier model changed, how
agent and human shopping processes differed) and draw the implications
for business, for policy, and for yourself as a consumer. Graded on
depth of analysis — not on how well your twin performed.

## What can go wrong at N=161, and the pre-decided answer

| Risk | Answer |
|---|---|
| A student's codespace won't build | Delete + recreate (fresh container). Second failure → pair up for today; the evidence pack is per-ID, sharing a machine sequentially is acceptable in extremis. |
| amazon.in blocks/locks an account from a datacenter IP | Do NOT burn class time fighting Amazon. Pre-decided fallback, built once before the week: the student re-runs the sessions against the sandbox store — books.toscrape.com, the same target as the smoke test (or the instructor-hosted mock shop if one was built) — using the synthetic persona. Same tasks, same deliverables, same packer, graded identically; the pack is flagged `sandbox` and excluded from the research dataset. Mild cases first try phone-hotspot browsing for the human session. |
| A student has no/near-empty Amazon order history | Agent bootstrap writes a thin profile and says so — which is itself analyzable (the persona-only twin). Flag these IDs; they are a natural comparison subgroup, not failures. |
| A run doesn't finish inside its slot | With 5 tasks the SOUL's ~10-min per-task cap means a worst-case run brushes the ~60-min slots — **verify 5-task run timing in the dry run** (tighten the per-task cap or trim to 4 categories if needed). A run that stalls is cut at the effort cap, the partner runs dtlab-cart on whatever is in the cart, and dtlab-verdict notes the truncation. Two lost runs ≠ a lost student: the pack validates what exists (a missing run is a named issue, the zip still builds) and the analyzer handles missing cells. |
| Wi-Fi collapse under simultaneous sessions | ~80 concurrent noVNC desktop streams at ~1–3 Mbps each ≈ 160–300 Mbps sustained through the room in long-lived websockets — a different profile from the browsing the room's "100 concurrent users" rating assumes. Verify with IT before the week: WAN headroom ≥ 2× that estimate; ≤ ~25–30 active clients per access point on 5/6 GHz; no captive-portal re-auth or websocket idle timeout inside a 3-hour window; no per-user throttle below ~3 Mbps. Students keep phones on mobile data (OTPs arrive there anyway). Decisive check: a 15–20 student pilot in the actual room measuring per-stream bitrate. The section split caps concurrency at ~80, never 161. |
| Claude API rate limits with ~80 concurrent agents per section | Rate limits are per student account (own accounts, own keys) — there is no shared pool. One agent makes ~4–12 requests/min, far below per-account limits, and prompt-cache reads are exempt from input-token limits. Residual risk is an account not set up in time: the pre-week checklist + Monday smoke test catch it; 2–3 course-owned spare keys cover stragglers. |
| Form submissions missing Sunday night | The batch script's roster output + one reminder mail. Persona generation takes seconds per student; a Monday-morning regeneration for stragglers is fine. |
