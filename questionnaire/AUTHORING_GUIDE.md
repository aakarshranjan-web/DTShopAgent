# The questionnaire instrument — format contract & maintenance

**STATUS: the instrument is authored.** `questionnaire_items.csv` now
contains the course's real **115 items**, generated from the authoritative
source document `questionnaire_instrument_source.md` (in this folder): 15
demographics, 57 validated-scale items (12 published scales, Toubia et al.
2025 battery), 22 amazon.in shopping-behavior items, 12 values/constraints
(VC01–VC05 are `constraint=1`), and 9 predictive items. Any change goes
into the source document FIRST, then is re-transferred to the CSV — the two
must never diverge. Everything downstream — the Google Form builder, the
persona generator, the agent's citation protocol (ECP), the research
schemas — reads the CSV and adapts automatically to codes, constructs, and
item count.

Three transfer conventions used (recorded so future edits stay
consistent): block stems are **embedded into each question** (e.g. "I see
myself as someone who…", "…as a guiding principle in your life?");
`likert5` anchors are the BFI-style set (Disagree strongly … Agree
strongly) defined in `build_form.gs`; and **en/em-dashes are flattened to
plain hyphens** in the CSV (Forms/CSV safety — the content-lockstep test
normalizes dashes when diffing, so this is the ONLY permitted typographic
divergence). D10 carries an added "Prefer not to say" option
(ethics-review decision, 2026-07-22).

## Column contract (dtlab-persona-v1)

| Column | Rules |
|---|---|
| `item_code` | Unique per row. Pattern: 1–4 letters + 1–3 digits (e.g. `D01`, `PS16`, `RISK07`). These codes become the citation vocabulary the agent must use in its decision log, and the join keys in the research dataset — choose codes you'll be happy to see in a results table. |
| `construct` | Free text; consecutive rows sharing the same value are grouped. The Form builder starts a new page whenever the text **before an optional colon** changes (so `Psychographics: brand` and `Psychographics: price` share one page titled "Psychographics"). Order your CSV so constructs are contiguous. |
| `question` | The verbatim question text. Avoid commas-inside-quotes headaches by keeping quoting clean, and avoid renaming questions inside the Form afterwards (the persona generator matches Form headers by the leading `CODE.` prefix). |
| `response_type` | One of `single_select`, `multi_select`, `likert5`, `short_text`, `long_text`. `likert5` renders the standard 5-point agree scale automatically; leave `options` empty for it and the text types. |
| `options` | Pipe-separated choices for `single_select` / `multi_select` (e.g. `Yes\|No\|Sometimes`). |
| `constraint` | `1` if a "yes"/non-empty answer must **override everything else** in the agent's decisions (allergies, dietary/religious rules, ethical exclusions, hard budget rules, materials avoided). `0` otherwise. Constraint items are flagged in the persona file and `SOUL.md` treats them as inviolable — this is how the constraints-always-win rule stays independent of your coding scheme. |

## Design notes (optional but recommended)

- The comparison memo bites hardest when a handful of items are *deliberately
  predictive* — e.g. "describe the gift you'd buy your closest friend for
  ₹1,500" gives you a direct stated-preference benchmark for the gift task.
- Keep at least a few stated-preference items that your students' purchase
  histories can contradict; the stated-vs-revealed conflicts are reliably the
  best material in the memos and in the cohort analysis.
- The item count lives in ONE place: `DTLAB_EXPECTED_ITEMS` in
  `dtlab_config.env` at the repo root (currently **115**, matching the
  instrument), with a matching fallback literal in
  `provisioning/student_start.sh`. If the instrument changes, update the
  config (and the fallback) together with the CSV —
  `tests/test_instrument_lockstep.py` fails on any divergence.

## Workflow to build the Form

0. Run `python3 tests/test_instrument_lockstep.py` — it must pass before
   you touch Google Forms (row count, code shapes, constraint flags,
   options discipline, config lockstep, and a full persona-generation
   round trip through `make_persona.py`).
1. Import the finished CSV into a Google Sheet, tab named `items`.
2. Run `buildForm()` from `build_form.gs` (Extensions → Apps Script).
   Confirm all 115 questions + 16 page breaks were created in one run
   (Apps Script quotas — a TODO(dry-run) item in `docs/CHANGELOG.md`).
3. Test-submit once; confirm the linked response Sheet headers carry the
   `CODE.` prefixes AND spot-check the anchor lists (AC 9-point, RF
   7-point, TS01 11-point, likert5 wording); delete the test row.
4. Freeze the instrument at Form build. Any post-launch edit = a new
   schema version (and a matching edit to
   `questionnaire_instrument_source.md`), re-checked by step 0.
