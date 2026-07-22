# Authoring your 100-item questionnaire

`questionnaire_items.csv` currently contains 6 EXAMPLE rows (codes EX01–EX06).
**Delete them and paste your own ~100 items in the same format.** Everything
downstream — the Google Form builder, the persona generator, the agent's
citation protocol, the research schemas — reads this one file and adapts
automatically to your codes, constructs, and item count.

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
- The item count is not enforced at exactly 100. Set `EXPECTED_ITEMS` at the
  top of `provisioning/student_start.sh` to your final count so the student
  pre-flight check validates completeness correctly.

## Workflow after authoring

1. Import your finished CSV into a Google Sheet, tab named `items`.
2. Run `buildForm()` from `build_form.gs` (Extensions → Apps Script).
3. Test-submit once; confirm the linked response Sheet headers carry your
   `CODE.` prefixes; delete the test row.
4. Freeze the instrument. Any post-launch edit = a new schema version.
