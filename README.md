# Digital Twin Shopping Agent Lab

Course + experiment kit: 180 MBA students each configure a Hermes agent
(Claude API backend) as their consumer digital twin, shop three tasks on
amazon.in themselves AND via their agent (counterbalanced, blinded), and
compare — producing a paired human/agent choice-and-process dataset.

**New here? Read `TA_ONBOARDING.md` first, then `COURSE_PLAN_1WEEK.md`.**
Run `bash tests/simulate_submission.sh` after touching the validation
chain. Never commit student data or keys (`.gitignore` covers the obvious
paths).

Turnkey package for the MBA module: Hermes Agent + Claude API + amazon.in,
with a research-grade data pipeline.

> **START HERE for the 180-student / one-week format: `COURSE_PLAN_1WEEK.md`.**
> It supersedes the long timeline and encodes three simplifications:
> the agent reads the purchase history itself on amazon.in (no extraction
> pipeline, `data-pipeline/` is now an optional research add-on),
> infrastructure is GitHub Codespaces on free personal accounts (no VMs,
> no Classroom), and the browsing-history toggle is optional (contamination
> is handled by the agent's search-only rule + the measured index).

## Contents

```
dt-lab/
├── README.md                          ← you are here
├── research_protocol.md               ← consent, pseudonyms, schemas, dataset assembly
├── agent/
│   └── SOUL.md                        ← agent identity + decision-log protocol (item-code citations)
├── questionnaire/
│   ├── questionnaire_items.csv        ← PLACEHOLDER (6 example rows) — instructor pastes their own ~100 items
│   ├── AUTHORING_GUIDE.md             ← column contract for authoring the instrument (incl. constraint flag)
│   ├── build_form.gs                  ← Apps Script: auto-builds the Google Form from the CSV
│   └── make_persona.py                ← Form responses row → persona_survey.md + .csv
├── TA_ONBOARDING.md                   ← start here: reading order + open work items
├── tests/simulate_submission.sh       ← regression harness for the whole validation chain (no browser needed)
├── docs/design_rationale.md           ← the rationale for all design choices: decision, the argument for it, the alternatives considered and why they were rejected, and where relevant the accepted risk with its price stated plainly.
├── COURSE_PLAN_1WEEK.md               ← THE operative plan: 2×3h sessions, N=180, overnight questionnaire
├── data-pipeline/                     ← OPTIONAL research add-on (post-course precise history via official export)
│   ├── clean_privacy_export.py        ← official Amazon export → schema v1
│   ├── scrape_orders.py               ← manual-login + Playwright scrape → schema v1
│   └── enrich_brands.py               ← resolves authoritative brand per ASIN
├── templates/
│   ├── tasks.md                       ← deliverable #3: the 3 tasks (instructor fills frames, student fills gift)
│   ├── human_picks.csv                ← deliverable #6: pre-registered student picks (structured)
│   └── comparison.md                  ← deliverable #7: per-task Verdict lines + assessment (machine-parsed)
├── tools/
│   └── pack_evidence.py               ← `dtlab-pack`: validates + bundles ALL 7 deliverables into one zip
├── PERSONALIZATION_PROTOCOL.md        ← Amazon's memory of the account: keep baseline personalization, reduce/block/measure within-experiment contamination
├── .devcontainer/                     ← devcontainer.json + setup.sh (AT REPO ROOT so Codespaces auto-detects it)
├── CLOUD_SETUP.md                     ← the Codespaces route (primary infra for the 1-week format)
└── provisioning/
    ├── VM_DISTRIBUTION.md             ← hypervisor choice + the staged testing funnel & triage table
    ├── host_check.sh / host_check.ps1 ← T-14 student-side host compatibility check (which image / Codespaces?)
    ├── provision.sh                   ← builds the golden VM image (instructor, once per architecture)
    └── student_start.sh               ← the one command students run (`dtlab-start`)
```

## The two-path history capture (why both scripts exist)

| | Privacy Central export (preferred) | Scraper (fallback / instant) |
|---|---|---|
| Accuracy | Authoritative unit price, qty, ASIN | Best-effort DOM parsing; per-item price occasionally missing |
| Speed | Request at T−14; usually arrives in hours–days, SLA up to ~1 month | ~4 s per order, immediate |
| Fragility | Stable file format | Breaks when Amazon changes its DOM — validate on dry run |
| ToS posture | Fully sanctioned (it's Amazon's own DSAR tool) | Automated access; mitigated by manual login + polite pacing, residual risk disclosed in syllabus |

Both emit the **identical schema (`dtlab-orders-v1`) + a provenance sidecar**,
so the cohort dataset is uniform regardless of path, with `capture_method` as
a covariate. Assign the export request at T−14; the scraper exists so nobody
is blocked on lab day. `enrich_brands.py` runs after either path.

## Questionnaire pipeline (Google Forms → Sheet → VM)

1. Instructor: author the instrument — replace the EX0x placeholder rows in
   `questionnaire_items.csv` with your own items per `AUTHORING_GUIDE.md`
   (unique codes, constructs, response types, and a `constraint` flag for
   inviolable items). Both the Form builder and the persona generator refuse
   to run while example rows remain. Then import the CSV into a Google Sheet
   (tab "items"), paste `build_form.gs` into Apps Script, run `buildForm()`.
   Link responses to a Sheet. **That response Sheet IS the cohort persona
   dataset** — one row per student, consistent coding, zero transcription.
2. Students complete the Form (~25 min) using their `DT2026-###` pseudonym.
3. Instructor exports the response Sheet as `responses.csv` and distributes
   it (or per-student slices).
4. Student, on the VM:
   `python3 ~/dtlab/tools/make_persona.py --responses responses.csv --student-id DT2026-042`
   → drops `persona_survey.md` (agent copy, item-coded) and
   `persona_survey.csv` (research copy) into the workspace.

Item codes are the connective tissue: the Form headers carry them, the
persona file preserves them, and `SOUL.md` obliges the agent to cite them in
its decision log — which is what makes the logs codeable into
`dtlab-choices-v1` and the citation-fidelity analysis possible. The pipeline
is agnostic to your coding scheme (any 1–4 letters + 1–3 digits) and item
count; if the final instrument isn't exactly 100 items, set `EXPECTED_ITEMS`
in `provisioning/student_start.sh` accordingly. Constraint semantics travel
via the CSV's `constraint` column → a `[CONSTRAINT]` flag in the persona
file → SOUL.md's constraints-always-win rule, so no item codes are ever
hard-coded anywhere.

## Claude API configuration

- One **Claude Platform workspace** for the course with a hard spend cap;
  issue one API key per student inside it (revoke all at T+8).
- During image build, run `hermes setup` and select **Anthropic** as
  provider with the key left blank; `dtlab-start` collects each student's
  key on first run.
- Model: default to **Claude Sonnet** (e.g. `claude-sonnet-4-6`) — ample for
  browser-loop shopping at a fraction of Opus cost. Budget guidance:
  a full three-task run is typically well under $1–2 in Sonnet tokens;
  cap keys at ~$8 to allow retries. Hermes supports Anthropic prompt
  caching, which helps because the persona + history are re-read each run.
- Verify caps on the Claude Console **dashboard**, not just in intent.

## Student experience (the whole thing, from their side)

1. Import the `.ova`, boot, log in.
2. Complete the Google Form (any device, before lab week).
3. (No data-export step — the agent reads the order history itself.)
4. Drop the persona files (batch-generated overnight by the instructor via
   `make_all_personas.py`) into `~/dtlab/workspace`. No history extraction:
   the agent reads Your Orders itself during its Bootstrap step.
5. **Shop first, logged:** run `dtlab-shop` — the student completes the
   three tasks THEMSELVES in an instrumented browser (clickstream logged:
   searches, product views, cart clicks), then confirms their 3 picks.
   Everything lands in `~/dtlab/human/`, which the agent is barred from
   reading. This ordering kills selection bias (they never see the agent
   think before choosing) AND warms the session with genuine human
   activity on a residential IP — the strongest CAPTCHA mitigation
   available without stealth tooling.
6. Agent second: `dtlab-record` in one terminal, `dtlab-start` in another
   (pre-flight refuses to launch until the human session exists, and
   refuses if human picks are found inside the agent workspace),
   `/browser connect` to the same warm profile, paste the task prompt,
   watch.
7. Screenshot cart into `~/dtlab/evidence/` → empty cart → fill
   `comparison.md` → run `dtlab-pack` → upload the single
   `DT2026-###_evidence.zip` it produces.

## The seven deliverables and how they're captured

| # | Deliverable | File in the submission zip | Produced by |
|---|---|---|---|
| 1 | Questionnaire with answers | `persona_survey.csv` + `.md` | Google Form → `make_persona.py` |
| 2 | Purchase history | `purchase_profile.md` — written by the agent itself from the logged-in Your Orders pages (mandatory Bootstrap in SOUL.md; capped at ~30 orders/12 months; every claim traceable to a seen order). Precise raw CSV only via the optional post-course add-on. | agent Bootstrap |
| 3 | The 3 tasks given to the agent | `tasks.md` | instructor frames + student's gift fields |
| 4 | Full agent trace | `decision_log.md` + `hermes_logs/` (session transcripts auto-collected since the run marker) | SOUL.md protocol + `dtlab-start` marker |
| 5 | 3 items the agent added to basket | `agent_picks.csv` (task_id, title, asin, price, sponsored) + `screenshots/` | SOUL.md protocol + student screenshot |
| 6 | 3 items the student chose + HOW they shopped | `human_picks.csv` + `human_session.jsonl` (clickstream: searches, product views, cart clicks, timestamps) | `dtlab-shop` (log_human_session.py), quarantined in `~/dtlab/human/` |
| 7 | Assessment / comparison per item | `comparison.md` with machine-parsed `Verdict:` lines (better / identical / equivalent / inferior, ASIN-cross-checked) | template |

`dtlab-pack` validates all seven (3 rows in each picks file, real ASINs,
verdicts present and consistent — it cross-checks each verdict against the
ASINs, enforcing 'identical' exactly when agent and student chose the same
product — no leftover placeholders), auto-collects Hermes session
logs modified since `dtlab-start` touched the run marker, computes SHA-256
hashes into `manifest.json`, and renders `report.html` — a single
self-contained page with the side-by-side picks table, verdicts, embedded
cart screenshot, and the decision log inline, so graders never unzip
anything. Invalid packs still produce the zip but exit non-zero and list
what to fix. Cohort assembly (research_protocol.md §5) then reduces to
concatenating the CSVs across zips — deliverables 1, 2, 5, 6 are already in
final schema, and 7's verdicts are regex-extractable (they're already in
each manifest.json).

Everything else — Hermes, Playwright, Chromium, SOUL.md, scripts, aliases —
is pre-baked into the image by `provision.sh`.

## Build checklist (instructor)

- [ ] Ethics/IRB approval + consent sheet (see research_protocol.md §3)
- [ ] Stage-0 dry run on three archetype machines (VM_DISTRIBUTION.md funnel)
- [ ] Publish image SHA-256 hashes next to download links
- [ ] Build Form via Apps Script; test-submit once; confirm response Sheet
- [ ] Build the golden image **twice** per VM_DISTRIBUTION.md: amd64 →
      `.ova` for VirtualBox (Windows/Intel Macs), arm64 → UTM bundle
      (Apple Silicon). Same `provision.sh` both times.
- [ ] **Dry run of the full path yourself** on the final image, ~3 weeks out:
      export request, both capture scripts (patch scraper selectors if the
      DOM drifted), persona generation, `/browser connect`, one full task.
- [ ] Claude workspace + per-student capped keys
- [ ] LMS: pre-registration form (timestamped), evidence upload slot
- [ ] Synthetic persona pack for opt-outs (fictional Form row + fabricated
      history CSV in schema v1 — generate once, reuse)

## Known-fragility register

1. **Hermes release drift** — commands/paths may shift between now and fall
   2026; the docs are canonical, the handout is best-effort.
2. **Amazon DOM drift** — affects `scrape_orders.py` and `enrich_brands.py`
   only; the SELECTORS dict is the single patch point.
3. **Installer URL** in `provision.sh` — verify against the official Nous
   Research site at image-build time.
4. **Form header parsing** in `make_persona.py` assumes titles keep their
   `CODE.` prefix — don't rename questions inside the Form after building.
5. **Placeholder instrument** — the kit ships with EX0x example rows only;
   the Form builder and persona generator hard-fail until the instructor's
   real items are in place (by design, so a placeholder can't silently reach
   students).
