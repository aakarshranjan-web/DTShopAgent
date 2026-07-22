# TA onboarding — Digital Twin Shopping Agent Lab

Welcome. This repo is the complete kit for the 1-week, 180-student
digital-twin experiment (Hermes Agent + Claude API + amazon.in).

## Read in this order (30 minutes)
1. `COURSE_PLAN_1WEEK.md` — THE operative plan (2×3h sessions, two arms).
2. `README.md` — file map + the seven deliverables and how each is captured.
3. `agent/SOUL.md` — the agent's identity, Bootstrap (it reads the user's
   amazon.in order history itself), logging protocol, hard boundaries.
4. `PERSONALIZATION_PROTOCOL.md` — the contamination model: pause
   Browsing History (Layer 1), agent search-only (2), measured index (3),
   counterbalanced blinded arms (4).
5. `research_protocol.md` — schemas, pseudonyms, consent, dataset assembly.
6. `questionnaire/AUTHORING_GUIDE.md` — instrument format (prof supplies
   the 100 items; the shipped CSV holds EX0x placeholders that HARD-FAIL
   all downstream tools until replaced).

## The student-facing surface (all of it)
Four commands inside a Codespace built from this repo:
`dtlab-shop` (logged own shopping) · `dtlab-start` (pre-flight + agent) ·
`dtlab-record` (screen capture) · `dtlab-pack` (validated submission zip).

## Your open work items (rough priority order)
- [ ] Turn this repo into a **template repo** (Settings → Template
      repository) after the professor's items land in
      `questionnaire/questionnaire_items.csv`.
- [ ] **Full dry run from a Codespace** against real amazon.in with a real
      account: build time, `hermes setup` flow, `/browser connect`,
      Bootstrap (order-history reading quality), one complete task,
      CAPTCHA frequency from Azure IPs. This dry run decides
      Codespaces-vs-fallback (see CLOUD_SETUP.md decision rule). Log
      every deviation from the docs — Hermes moves fast; our pinned
      commands may lag a release.
- [ ] Validate the fragile DOM-dependent code against live amazon.in:
      `tools/log_human_session.py` (cart-click selector, URL parsing) and,
      only if the research add-on is used, `data-pipeline/scrape_orders.py`
      (SELECTORS dict is the single patch point).
- [ ] Claude Console: course workspace, hard cap, generate 180 keys via
      the Admin API (script it), map key→pseudonym→LMS distribution.
- [ ] Build the arm-randomization list (stratified; H_FIRST/A_FIRST) and
      the LMS assignment sheet BEFORE session 2.
- [ ] Create the synthetic persona pack (fictional Form row + a fictional
      order history narrative) for opt-out students.
- [ ] Run `tests/simulate_submission.sh` after ANY change to
      `tools/pack_evidence.py`, `templates/`, or `agent/SOUL.md`'s
      logging/picks protocol — it regression-tests the whole validation
      chain without a browser.
- [ ] Wi-Fi capacity check with facilities for 180 concurrent noVNC
      streams; decide on cohort staggering (2×90) if weak.

## Things you must NOT do
- Commit any student data or API keys (`.gitignore` blocks the obvious
  paths — think before you `git add -f`).
- Weaken the bias quarantine (`~/dtlab/human/` vs agent workspace) or the
  arm-aware ordering checks in `pack_evidence.py`; they are what makes
  the experiment defensible.
- "Fix" CAPTCHA friction with stealth/evasion tooling — out of scope by
  design (see the ethics sections).

## License / sharing
No license file yet — ask the professor before making the repo public or
reusing outside the course.
