#!/usr/bin/env python3
"""
make_persona.py — Turn one student's row of the Google Form response sheet
into the Hermes-ready persona files.

INPUTS
  --items      questionnaire_items.csv (the instrument; defines codes/constructs)
  --responses  responses.csv (File > Download > CSV from the linked response
               Sheet — the instructor distributes this, or each student
               downloads it and the script picks out only their own row)
  --student-id the pseudonym to extract (e.g. DT2026-042)

OUTPUTS (drop both into the Hermes workspace)
  persona_survey.md   — human/agent-readable, grouped by construct,
                        each answer tagged with its item code so the agent's
                        decision log can cite "PS16" verbatim
  persona_survey.csv  — flat machine-readable copy (item_code, construct,
                        question, answer) for the research dataset

USAGE
  python3 make_persona.py --items questionnaire_items.csv \
      --responses responses.csv --student-id DT2026-042
"""

import argparse
import csv
import re
import sys
from collections import OrderedDict
from pathlib import Path

# Matches any code of 1-4 letters + 1-3 digits at the start of a Form header,
# e.g. "D01.", "PS16.", "RISK07." — see AUTHORING_GUIDE.md column contract.
CODE_RE = re.compile(r"^([A-Z]{1,4}\d{1,3})\.")


def load_items(path):
    items = OrderedDict()
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("item_code"):
                items[r["item_code"]] = r
    return items


def find_student_row(path, student_id):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        id_col = next((h for h in reader.fieldnames
                       if "participant id" in h.lower()
                       or "DT2026" in h or "course-issued" in h.lower()), None)
        if not id_col:
            sys.exit("Could not find the participant-ID column in responses.csv")
        for row in reader:
            if row.get(id_col, "").strip() == student_id:
                return row, reader.fieldnames
    sys.exit(f"No response row found for {student_id}. "
             f"Check the ID and that the form was submitted.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="questionnaire_items.csv")
    ap.add_argument("--responses", required=True)
    ap.add_argument("--student-id", required=True)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    items = load_items(args.items)
    if any(c.startswith("EX0") for c in items):
        sys.exit("questionnaire_items.csv still contains EX0x example rows — "
                 "replace them with the course's real items "
                 "(see AUTHORING_GUIDE.md).")
    row, headers = find_student_row(args.responses, args.student_id)

    # Form question headers look like "PS16. 'Only 2 left in stock'..."
    answers = OrderedDict()
    for h in headers:
        m = CODE_RE.match(h.strip())
        if m and m.group(1) in items:
            val = (row.get(h) or "").strip()
            # strip Likert prefix "4 - Agree" -> keep both number and label
            answers[m.group(1)] = val

    missing = [c for c in items if c not in answers]
    if missing:
        print(f"WARNING: {len(missing)} items missing from responses "
              f"(first few: {missing[:5]}). Continuing.", file=sys.stderr)

    outdir = Path(args.outdir)

    # ---- persona_survey.csv (research copy) ----
    with open(outdir / "persona_survey.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id", "item_code", "construct",
                    "question", "answer", "constraint"])
        for code, item in items.items():
            w.writerow([args.student_id, code, item["construct"],
                        item["question"], answers.get(code, ""),
                        item.get("constraint", "0") or "0"])

    # ---- persona_survey.md (agent copy) ----
    lines = [
        f"# Consumer profile — participant {args.student_id}",
        "",
        f"Source: {len(items)}-item Digital Twin questionnaire "
        "(dtlab-persona-v1).",
        "Cite item codes verbatim when using these facts in the decision log.",
        "Likert answers: 1=Strongly disagree ... 5=Strongly agree.",
        "Items marked [CONSTRAINT] are inviolable rules, never preferences.",
        "",
    ]
    current = None
    for code, item in items.items():
        if item["construct"] != current:
            current = item["construct"]
            lines += [f"## {current}", ""]
        ans = answers.get(code, "(no answer)")
        flag = " **[CONSTRAINT]**" if str(
            item.get("constraint", "0")).strip() == "1" else ""
        lines.append(f"- **{code}**{flag} {item['question']}  \n  → {ans}")
    (outdir / "persona_survey.md").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")

    print(f"Wrote persona_survey.md and persona_survey.csv for "
          f"{args.student_id} ({len(answers)}/{len(items)} items answered).")


if __name__ == "__main__":
    main()
