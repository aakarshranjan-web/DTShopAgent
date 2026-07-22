# Research protocol — Digital Twin Shopping Agent Lab
**Data schemas, pseudonymization, consent, and cohort dataset assembly**
Version: dtlab-protocol-v1 (July 2026)

## 1. What the study yields

Per participant (N = cohort size), the design produces a paired-choice dataset:

| Unit | Variables |
|---|---|
| Participant | ~100 coded questionnaire items (dtlab-persona-v1, instructor-authored instrument); purchase profile as agent-extracted `purchase_profile.md` (traceable-claims rule in SOUL.md; precise dtlab-orders-v1 CSV only for the optional post-course export add-on subgroup); demographics |
| Participant × session | human shopping-process clickstream (dtlab-humanlog-v1): search queries, product views (ASIN + dwell sequence), cart-add clicks, filters/sorts — captured passively by log_human_session.py BEFORE the agent runs |
| Task × participant (3 per participant) | human pick made first (uncontaminated: the student never sees the agent before choosing) (title, ASIN, price, stated reasoning), agent pick (title, ASIN, price), agent decision log with item-code citations, sponsored-listing flag, human intervention count, student's better/worse/equal/different verdict |

Participants are randomized into counterbalanced order arms (H_FIRST /
A_FIRST with blinding; PERSONALIZATION_PROTOCOL.md Layer 4), with arm
recorded in every manifest. Analyze arm as a design factor; test the
order effect with a pre-registered equivalence margin (TOST), not a bare
null-hypothesis test.

This supports at minimum: PROCESS comparison between human and agent
shopping (consideration-set size and overlap, query formulation, search
depth, dwell allocation, sponsored exposure) — arguably the most novel
contribution, since outcome agreement with divergent processes and process
mimicry with divergent outcomes are entirely different twin properties;
human–agent agreement rates by task type (with the per-participant
contamination index from each manifest as a covariate — see
PERSONALIZATION_PROTOCOL.md); price-delta
analysis; sponsored-capture analysis; the identical-vs-equivalent split (exact
product convergence vs. functional substitution) as a twin-fidelity
measure; which questionnaire constructs predict
agreement (feature-importance on persona items); stated-vs-revealed preference
conflicts and how the agent resolved them; and citation-fidelity analysis
(are the agent's cited profile facts real or confabulated — connect to your
GenAI quality-assurance metascience agenda).

## 2. Pseudonymization

- Each student receives a course-issued ID: `DT2026-###`. The ID ↔ name
  mapping lives in ONE file, held by the instructor, stored separately from
  all research data, deleted at end of study.
- Every artifact (questionnaire row, purchase CSV, decision log, evidence
  pack) carries only the pseudonym. Scripts enforce this: `student_id` is a
  required argument and the Form validates the ID pattern.
- The Google Form collects institutional email for submission integrity;
  before analysis, export the response sheet, verify one-row-per-ID, then
  DELETE the email column from the research copy.

## 3. Consent and opt-out

- Written information sheet + consent BEFORE the questionnaire opens.
  Consent covers: (a) use of pseudonymized questionnaire responses,
  purchase-history extracts, and agent logs for research and potential
  publication; (b) that participation in the *course exercise* is required
  but inclusion in the *research dataset* is optional and separable;
  (c) right to withdraw data until the anonymization/analysis date. The
  consent sheet must explicitly cover the shopping-session clickstream
  (what is captured, what is excluded, that it stays local until packed).
- Non-consenting or opt-out students use the synthetic persona pack; their
  course grade is unaffected and their data never enters the dataset.
- Obtain ethics/IRB approval from your institution before the questionnaire
  opens (UNC and/or WU Vienna depending on where the cohort sits — note EU
  students bring GDPR obligations: purchase history is personal data;
  lawful basis = consent; minimization is implemented in the pipeline).

## 4. Data-minimization guarantees (implemented in code)

- `clean_privacy_export.py` / `scrape_orders.py` write ONLY:
  `student_id, order_date, brand, product_title, asin, unit_price_inr,
  quantity, capture_method` (+ provenance sidecar). Order IDs, addresses,
  payment data, and carrier data never reach the workspace or the dataset.
- `student_start.sh` refuses to launch if raw export files or PII-named
  files sit in the agent workspace.
- API keys are course-issued from one Claude Platform workspace with a hard
  workspace spend cap and per-key limits; all keys are revoked at T + 8.

## 5. Cohort dataset assembly (instructor, after T + 7)

Students submit ONE zip to the LMS: `DT2026-###_evidence.zip`, produced and
validated by `dtlab-pack` (tools/pack_evidence.py). It contains all seven
deliverables plus `manifest.json` (SHA-256 hashes, validation results,
extracted verdicts) and `report.html` (grader view). Screen recordings are
uploaded separately due to size; the zip's RECORDINGS.txt indexes them.

Assembly steps:
1. Concatenate all `persona_survey.csv` → `cohort_personas.csv`.
2. Concatenate all `purchase_history.csv` → `cohort_orders.csv` (the
   provenance sidecars give you capture-method covariates).
3. Build `cohort_choices.csv` by joining each zip's `agent_picks.csv`,
   `human_picks.csv`, and manifest verdicts (all machine-readable); only
   `cited_codes` / `citation_valid_share` require coding from the decision
   logs, and those follow the numbered SOUL.md protocol.
4. Join on `student_id` + task number. Freeze, hash, archive.

## 6. Schema registry

- `dtlab-persona-v1`: student_id, item_code, construct, question, answer,
  constraint {0|1}. Item codes/constructs are instructor-defined; the
  instrument is frozen at Form launch and versioned thereafter.
- `dtlab-orders-v1`: student_id, order_date, brand_guess[/brand,
  brand_source], product_title, asin, unit_price_inr, quantity,
  capture_method.
- `dtlab-humanlog-v1` (JSONL events): ts, student_id, type
  {session_start|search|product_view|cart_add|filter_sort|nav|session_end},
  plus type-specific fields (query/page/sort; asin/title). Checkout,
  payment, and auth paths are never logged; non-amazon browsing is never
  logged.
- `dtlab-choices-v1` (coded from logs): student_id, task_id, chooser
  {human|agent}, asin, title, price_inr, sponsored {0|1}, n_candidates,
  n_interventions, verdict {better|identical|equivalent|inferior} (agent choice relative to the participant's own pre-registered pick; 'identical' is ASIN-verified by the packer, so it is an objective category while the other three are the participant's judgment), cited_codes
  (pipe-list), citation_valid_share (0–1).

Version any change; never mutate a frozen schema.
