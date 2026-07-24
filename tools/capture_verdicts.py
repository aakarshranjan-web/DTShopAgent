#!/usr/bin/env python3
"""
capture_verdicts.py — `dtlab-verdict`: guided, structured verdict capture
(replaces hand-editing the comparison memo — format errors at N=161 were
the failure mode).

For every task x started agent run it prompts, input-validated:
  - verdict: better | identical | equivalent | inferior
    ('identical' is ASIN-checked live against your pick and the agent's,
    and re-verified by the packer)
  - your own-pick rating and the agent-pick rating (1-10)
  - a one-line rationale
then the per-task head-to-heads (grounding winner per tier, tier winner
per grounding — only for contrasts whose two runs both exist) and, once
all four runs are captured, the Overall reflection questions.

Writes (schema dtlab-verdicts-v1, research_protocol.md §6):
  ~/dtlab/workspace/verdicts.csv           student_id, task_id, condition,
                                           tier, verdict, rating_self,
                                           rating_agent, rationale
  ~/dtlab/workspace/head_to_heads.csv      task_id, contrast, winner
  ~/dtlab/workspace/overall_reflections.md free text

Idempotent and resumable: Thursday fills the economy rows, Friday the
rest; re-running shows the stored answer and Enter keeps it.
"""

import csv
import re
import sys
from pathlib import Path

HOME = Path.home()
WS = HOME / "dtlab" / "workspace"
HU = HOME / "dtlab" / "human"
HOLD = HOME / "dtlab" / "persona_hold"
RUNSDIR = HOME / "dtlab" / "runs"
VERDICTS = ("better", "identical", "equivalent", "inferior")
VERDICT_HELP = ("better     = the agent's choice is BETTER for me than my own pick\n"
                "identical  = same product (same ASIN) as mine\n"
                "equivalent = different product, equally good fit for me\n"
                "inferior   = the agent's choice is WORSE for me")
# canonical 2x2 Overall questions — keep in lockstep with
# make_task_docs.py::OVERALL_ABLATION (same five, same order)
OVERALL_QUESTIONS = (
    "1. What did the questionnaire demonstrably add over your purchase "
    "history alone — and where did the ablated twin do just as well or "
    "better?",
    "2. Constraints: your CONSTRAINT items (allergies, exclusions) were "
    "absent in the ablated runs. Did their picks violate any? What does "
    "that imply for real deployment?",
    "3. Tier: what did the frontier model demonstrably buy over the "
    "economy model — and was it worth ~10x the token price?",
    "4. Delegation: which twin (if any) would you give real spending "
    "authority with a cap, and for which categories?",
    "5. The one change that would most improve your twin:",
)


def read_csv_rows(p):
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def find_student_id():
    for p in (WS / "persona_survey.csv", HOLD / "persona_survey.csv"):
        rows = read_csv_rows(p)
        if rows and rows[0].get("student_id"):
            return rows[0]["student_id"].strip()
    return None


def load_task_ids():
    p = HOME / "dtlab" / "tasks_config.csv"
    ids = [r["task_id"].strip() for r in read_csv_rows(p)
           if (r.get("task_id") or "").strip()
           and not r["task_id"].strip().startswith("#")]
    return ids or ["1", "2", "3"]


def load_runs():
    """Started runs -> [(runN, condition, tier)] in run order. Tier falls
    back by run index for packs from before per-run tier files."""
    runs = []
    for i in (1, 2, 3, 4):
        d = RUNSDIR / f"run{i}"
        if not d.exists():
            continue
        cond = (d / "condition.txt").read_text().strip() \
            if (d / "condition.txt").exists() else ""
        tier = (d / "tier.txt").read_text().strip() \
            if (d / "tier.txt").exists() else \
            ("economy" if i <= 2 else "frontier")
        if cond in ("persona", "ablated"):
            runs.append((f"run{i}", cond, tier))
    return runs


def picks_by_task(path):
    return {str(r.get("task_id", "")).strip(): r
            for r in read_csv_rows(path)}


def ask(prompt, valid, current=None, allow_empty=False):
    """Validated input; Enter keeps `current` when one exists."""
    suffix = f" [{current}]" if current else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip().lower()
        if not raw:
            if current:
                return current
            if allow_empty:
                return ""
        if raw in valid:
            return raw
        print(f"    one of: {' | '.join(sorted(valid))}")


def ask_rating(prompt, current=None):
    suffix = f" [{current}]" if current else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw and current:
            return current
        if re.fullmatch(r"(10|[1-9])", raw):
            return raw
        print("    whole number 1-10")


def ask_line(prompt, current=None):
    suffix = " [Enter keeps stored answer]" if current else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    return raw or (current or "")


def ask_block(prompt, current=None):
    """Multiline free text; finish with an empty line. Immediate Enter
    keeps the stored answer."""
    suffix = " [Enter keeps stored answer]" if current else ""
    print(f"{prompt}{suffix} — finish with an empty line:")
    lines = []
    while True:
        raw = input("  ")
        if not raw.strip():
            break
        lines.append(raw.rstrip())
    return "\n".join(lines) or (current or "")


def main():
    student_id = find_student_id()
    if "--student-id" in sys.argv:
        student_id = sys.argv[sys.argv.index("--student-id") + 1]
    if not student_id:
        sys.exit("cannot determine student_id (persona_survey.csv missing? "
                 "use --student-id DT2026-###)")
    task_ids = load_task_ids()
    runs = load_runs()
    if not runs:
        sys.exit("no agent runs found under ~/dtlab/runs — dtlab-verdict "
                 "runs AFTER the day's agent runs.")
    human = picks_by_task(HU / "human_picks.csv")

    # ---- per task x run: verdict + ratings + rationale ----
    vpath = WS / "verdicts.csv"
    stored = {(r.get("task_id", "").strip(), r.get("condition", "").strip(),
               r.get("tier", "").strip()): r for r in read_csv_rows(vpath)}
    print(f"\ndtlab-verdict — {student_id}. Runs on file: " +
          ", ".join(f"{rn} ({c}, {t})" for rn, c, t in runs))
    print("Enter keeps a stored answer; everything is revisable by "
          "re-running dtlab-verdict.\n")
    out_rows = []
    for rn, cond, tier in runs:
        agent = picks_by_task(RUNSDIR / rn / "agent_picks.csv")
        print(f"=== {rn}: {cond} run, {tier} tier ===")
        for t in task_ids:
            cur = stored.get((t, cond, tier), {})
            a, h = agent.get(t, {}), human.get(t, {})
            a_asin = (a.get("asin") or "").strip()
            h_asin = (h.get("asin") or "").strip()
            print(f"\n  Task {t}")
            if h:
                print(f"    your pick : {h.get('title', '?')[:70]} "
                      f"({h_asin})")
            if a:
                print(f"    agent pick: {a.get('title', '?')[:70]} "
                      f"({a_asin})")
            if a_asin and h_asin:
                if a_asin == h_asin:
                    print("    (same ASIN — verdict must be 'identical')")
                    valid = {"identical"}
                else:
                    valid = {"better", "equivalent", "inferior"}
            else:
                valid = set(VERDICTS)
            cur_v = (cur.get("verdict") or "").strip() or None
            if cur_v not in valid:
                cur_v = None
            v = ask("    verdict (better/identical/equivalent/inferior)",
                    valid, cur_v)
            rs = ask_rating("    YOUR pick — satisfaction owning it (1-10)",
                            (cur.get("rating_self") or "").strip() or None)
            ra = ask_rating("    AGENT pick — satisfaction owning it (1-10)",
                            (cur.get("rating_agent") or "").strip() or None)
            why = ask_line("    one-line rationale",
                           (cur.get("rationale") or "").strip() or None)
            out_rows.append({
                "student_id": student_id, "task_id": t,
                "condition": cond, "tier": tier, "verdict": v,
                "rating_self": rs, "rating_agent": ra, "rationale": why})
    with open(vpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "student_id", "task_id", "condition", "tier", "verdict",
            "rating_self", "rating_agent", "rationale"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nWrote {vpath} ({len(out_rows)} rows, schema dtlab-verdicts-v1)")

    # ---- per-task head-to-heads (only contrasts whose cells both ran) ----
    cells = {(c, t) for _, c, t in runs}
    hpath = WS / "head_to_heads.csv"
    hstored = {(r.get("task_id", "").strip(), r.get("contrast", "").strip()):
               (r.get("winner") or "").strip()
               for r in read_csv_rows(hpath)}
    hrows = []
    contrasts = []
    for tier in ("economy", "frontier"):
        if {("persona", tier), ("ablated", tier)} <= cells:
            contrasts.append((f"grounding_{tier}",
                              f"winner ({tier}): which GROUNDING chose "
                              "better for you", {"persona", "ablated",
                                                 "tie"}))
    for cond in ("persona", "ablated"):
        if {(cond, "economy"), (cond, "frontier")} <= cells:
            contrasts.append((f"tier_{cond}",
                              f"better model ({cond} runs): which TIER "
                              "chose better for you", {"frontier",
                                                       "economy", "same"}))
    if contrasts:
        print("\n=== Head-to-heads (compare the runs' picks directly) ===")
        for fam, label, valid in contrasts:
            for t in task_ids:
                cur = hstored.get((t, fam)) or None
                if cur not in valid:
                    cur = None
                w = ask(f"  Task {t} {label}", valid, cur)
                hrows.append({"task_id": t, "contrast": fam, "winner": w})
        with open(hpath, "w", newline="", encoding="utf-8") as f:
            wcsv = csv.DictWriter(f, fieldnames=["task_id", "contrast",
                                                 "winner"])
            wcsv.writeheader()
            wcsv.writerows(hrows)
        print(f"Wrote {hpath}")

    # ---- Overall reflections (after the full 2x2 exists) ----
    opath = WS / "overall_reflections.md"
    if len(runs) >= 4:
        print("\n=== Overall reflections (a few sentences each) ===")
        existing = opath.read_text(encoding="utf-8") if opath.exists() \
            else ""
        answers = []
        for i, q in enumerate(OVERALL_QUESTIONS, 1):
            # stored answer = text after the question's blank line
            m = re.search(rf"(?ms)^## Q{i}\n.*?\n\n(.*?)\n?(?=^## Q|\Z)",
                          existing)
            cur = (m.group(1).strip() or None) if m else None
            print(f"\n{q}")
            a = ask_block("  answer", cur)
            answers.append((q, a))
        opath.write_text(
            f"# Overall reflections — {student_id}\n\n" +
            "\n".join(f"## Q{i}\n{q}\n\n{a}\n"
                      for i, (q, a) in enumerate(answers, 1)),
            encoding="utf-8")
        print(f"\nWrote {opath}")
    else:
        print("\n(Overall reflections are asked once all four runs exist — "
              "re-run dtlab-verdict after the day-2 runs.)")

    print("\nDone. Next: after the final day's runs — dtlab-pack.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
