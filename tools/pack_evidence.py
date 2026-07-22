#!/usr/bin/env python3
"""
pack_evidence.py — collect, validate, and bundle ALL SEVEN deliverables into
one submission file:  ~/dtlab/<STUDENT_ID>_evidence.zip

  #1 persona_survey.csv + .md      (questionnaire with answers)
  #2 purchase_history.csv (+provenance sidecar)
  #3 tasks.md                      (the 3 tasks given to the agent)
  #4 hermes_logs/ + decision_log.md (full agent trace)
  #5 agent_picks.csv + cart screenshot(s)  (what the agent added to basket)
  #6 human_picks.csv               (what the student chose, pre-registered)
  #7 comparison.md                 (per-task verdicts + assessment)

Also writes report.html inside the zip: a single self-contained page a grader
can open — side-by-side picks table, verdicts, embedded cart screenshot, and
the decision log / comparison inline. Plus manifest.json with SHA-256 hashes
and validation results (research integrity: hash before you grade).

Run on the VM:   dtlab-pack        (alias for: python3 ~/dtlab/tools/pack_evidence.py)
Exit code is non-zero if any REQUIRED component is missing/invalid, and the
zip is still produced with the manifest marking what failed.
"""

import base64
import csv
import hashlib
import html
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
WS = HOME / "dtlab" / "workspace"
EV = HOME / "dtlab" / "evidence"
HU = HOME / "dtlab" / "human"      # human shopping log + picks (agent-quarantined)
MARKER = HOME / "dtlab" / ".run_started"   # touched by dtlab-start
HERMES_DIRS = [HOME / ".hermes", HOME / ".config" / "hermes"]
VERDICTS = {"better", "identical", "equivalent", "inferior"}
MAX_LOG_MB = 50

issues = []


def need(cond, msg):
    if not cond:
        issues.append(msg)
    return cond


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def find_student_id():
    p = WS / "persona_survey.csv"
    if p.exists():
        rows = read_csv(p)
        if rows and rows[0].get("student_id"):
            return rows[0]["student_id"].strip()
    return None


def collect_hermes_logs(staging):
    """Copy session/transcript/log files modified since the run marker."""
    out = staging / "hermes_logs"
    out.mkdir(parents=True, exist_ok=True)
    since = MARKER.stat().st_mtime if MARKER.exists() else 0
    n, total = 0, 0
    for root in HERMES_DIRS:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in {".jsonl", ".json", ".log", ".md",
                                        ".txt"}:
                continue
            if f.stat().st_mtime < since:
                continue
            # never pack credentials/config
            if any(s in f.name.lower() for s in
                   ("key", "secret", "credential", "auth", "env", "config")):
                continue
            total += f.stat().st_size
            if total > MAX_LOG_MB * (1 << 20):
                break
            dest = out / f"{f.parent.name}__{f.name}"
            shutil.copy2(f, dest)
            n += 1
    return n


def picks_table(agent, human):
    rows = []
    for t in ("1", "2", "3"):
        a = next((r for r in agent if str(r.get("task_id", "")).strip() == t),
                 {})
        h = next((r for r in human if str(r.get("task_id", "")).strip() == t),
                 {})
        rows.append((t, h.get("title", "—"), h.get("price_inr", ""),
                     a.get("title", "—"), a.get("price_inr", ""),
                     a.get("sponsored", "")))
    return rows


def build_report(staging, student_id, verdicts, table, screenshots):
    def esc(s):
        return html.escape(str(s))
    shots = ""
    for s in screenshots[:2]:
        b64 = base64.b64encode(s.read_bytes()).decode()
        mime = "image/png" if s.suffix.lower() == ".png" else "image/jpeg"
        shots += (f'<img src="data:{mime};base64,{b64}" '
                  f'style="max-width:100%;border:1px solid #ccc;margin:8px 0">')
    trs = "".join(
        f"<tr><td>{t}</td><td>{esc(ht)}</td><td>{esc(hp)}</td>"
        f"<td>{esc(at)}</td><td>{esc(ap)}</td><td>{esc(sp)}</td>"
        f"<td><b>{esc(verdicts.get(t, '?'))}</b></td></tr>"
        for t, ht, hp, at, ap, sp in table)

    def inline(name):
        p = staging / name
        return (f"<h2>{name}</h2><pre>{esc(p.read_text(encoding='utf-8'))}"
                "</pre>") if p.exists() else ""

    doc = f"""<!doctype html><meta charset="utf-8">
<title>DT Lab submission — {esc(student_id)}</title>
<style>body{{font-family:system-ui;max-width:960px;margin:2em auto;
padding:0 1em}}table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #bbb;padding:6px;font-size:14px;vertical-align:top}}
pre{{white-space:pre-wrap;background:#f6f6f6;padding:1em;font-size:13px}}
h1,h2{{border-bottom:2px solid #eee;padding-bottom:4px}}</style>
<h1>Digital Twin Lab — {esc(student_id)}</h1>
<p>Packed {datetime.now(timezone.utc).isoformat()} UTC.
Validation issues: {len(issues)} {esc('; '.join(issues)) if issues else '(none)'}</p>
<h2>Human vs. agent picks</h2>
<table><tr><th>Task</th><th>Human pick</th><th>Rs.</th><th>Agent pick</th>
<th>Rs.</th><th>Sponsored?</th><th>Verdict</th></tr>{trs}</table>
<h2>Cart evidence</h2>{shots or '<p>(no screenshot found)</p>'}
{inline('comparison.md')}
{inline('decision_log.md')}
{inline('tasks.md')}
"""
    (staging / "report.html").write_text(doc, encoding="utf-8")


def main():
    student_id = find_student_id() or (
        sys.argv[sys.argv.index("--student-id") + 1]
        if "--student-id" in sys.argv else None)
    need(student_id, "cannot determine student_id "
                     "(persona_survey.csv missing? use --student-id)")
    student_id = student_id or "UNKNOWN"

    staging = HOME / "dtlab" / f"_staging_{student_id}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    # ---- #1, #2, #3, #4(decision log), #5(picks), #6, #7: copy from WS ----
    required = ["persona_survey.csv", "persona_survey.md",
                "purchase_profile.md", "tasks.md", "decision_log.md",
                "agent_picks.csv", "comparison.md"]
    # optional: only present if the (research add-on) extraction path was used
    optional = ["purchase_history.csv", "purchase_history_provenance.json"]
    for name in required:
        src = WS / name
        if need(src.exists(), f"missing {name}"):
            shutil.copy2(src, staging / name)
    for name in optional:
        if (WS / name).exists():
            shutil.copy2(WS / name, staging / name)

    # human-side artifacts live OUTSIDE the agent workspace (bias quarantine)
    for name, req in (("human_picks.csv", True),
                      ("human_session.jsonl", True)):
        src = HU / name
        if need(src.exists(), f"missing {name} in ~/dtlab/human/ "
                              "(run dtlab-shop first)") or not req:
            if src.exists():
                shutil.copy2(src, staging / name)
    need(not (WS / "human_picks.csv").exists(),
         "human_picks.csv found INSIDE the agent workspace — bias "
         "quarantine violated; keep human files in ~/dtlab/human/ only")
    # arm-aware ordering check against the agent run marker
    armfile = HOME / "dtlab" / "arm.txt"
    arm = armfile.read_text().strip() if armfile.exists() else "UNKNOWN"
    need(arm in ("H_FIRST", "A_FIRST"),
         "experimental arm not recorded — run dtlab-start once to set it")
    hs = HU / "human_session.jsonl"
    if hs.exists() and MARKER.exists():
        if arm == "H_FIRST":
            need(hs.stat().st_mtime <= MARKER.stat().st_mtime + 300,
                 "H_FIRST arm: human_session.jsonl was modified AFTER the "
                 "agent run started — ordering violated")
        elif arm == "A_FIRST":
            need(hs.stat().st_mtime >= MARKER.stat().st_mtime - 300,
                 "A_FIRST arm: human session predates the agent run — "
                 "ordering violated")

    # ---- validations ----
    agent = read_csv(staging / "agent_picks.csv") \
        if (staging / "agent_picks.csv").exists() else []
    human = read_csv(staging / "human_picks.csv") \
        if (staging / "human_picks.csv").exists() else []
    if (staging / "human_session.jsonl").exists():
        ev_lines = (staging / "human_session.jsonl").read_text(
            encoding="utf-8").strip().splitlines()
        n_search = sum(1 for l in ev_lines if '"type": "search"' in l
                       or '"type":"search"' in l)
        n_views = sum(1 for l in ev_lines if '"product_view"' in l)
        need(n_views >= 3, f"human_session.jsonl has only {n_views} product "
                           "views — did the logger run during shopping?")
    else:
        n_search = n_views = 0
    need(len(agent) == 3, f"agent_picks.csv has {len(agent)} rows, need 3")
    need(len(human) == 3, f"human_picks.csv has {len(human)} rows, need 3")
    need(not any("REPLACE" in json.dumps(r) for r in human),
         "human_picks.csv still contains REPLACE placeholders")
    for r in agent:
        need(re.fullmatch(r"[A-Z0-9]{10}", r.get("asin", "").strip() or ""),
             f"agent pick task {r.get('task_id')}: bad/missing ASIN")

    verdicts = {}
    comp = staging / "comparison.md"
    if comp.exists():
        text = comp.read_text(encoding="utf-8")
        for m in re.finditer(r"##\s*Task\s*(\d)[\s\S]*?Verdict:\s*(\w+)",
                             text):
            verdicts[m.group(1)] = m.group(2).lower()
        need(all(verdicts.get(t) in VERDICTS for t in ("1", "2", "3")),
             "comparison.md: each Task needs 'Verdict: "
             "better|identical|equivalent|inferior'")
        # Cross-check verdicts against ASINs: "identical" iff same product
        for t in ("1", "2", "3"):
            a = next((r.get("asin", "").strip() for r in agent
                      if str(r.get("task_id", "")).strip() == t), "")
            h = next((r.get("asin", "").strip() for r in human
                      if str(r.get("task_id", "")).strip() == t), "")
            v = verdicts.get(t)
            if a and h and v:
                need(not (a == h and v != "identical"),
                     f"task {t}: agent and you picked the SAME ASIN ({a}) "
                     f"— verdict must be 'identical', not '{v}'")
                need(not (a != h and v == "identical"),
                     f"task {t}: verdict 'identical' but ASINs differ "
                     f"(agent {a} vs yours {h}) — use "
                     f"better/equivalent/inferior")
        need("{" not in text.split("## Overall")[0] or
             "{STUDENT_ID}" not in text,
             "comparison.md still contains template placeholders")

    # ---- #4: hermes session logs; #5: screenshots; recording note ----
    n_logs = collect_hermes_logs(staging)
    need(n_logs > 0, "no Hermes session logs found since run start "
                     "(did dtlab-start create the run marker?)")
    screenshots = sorted(list(EV.glob("*.png")) + list(EV.glob("*.jpg")))
    need(len(screenshots) > 0, "no cart screenshot in ~/dtlab/evidence/")
    shots_dir = staging / "screenshots"
    shots_dir.mkdir(exist_ok=True)
    for s in screenshots:
        shutil.copy2(s, shots_dir / s.name)
    recordings = list(EV.glob("run_*.mkv"))
    (staging / "RECORDINGS.txt").write_text(
        "Screen recordings are uploaded separately (size):\n" +
        "\n".join(f"{r.name}  {r.stat().st_size >> 20} MB"
                  for r in recordings) + "\n" if recordings
        else "No screen recording found.\n")

    # ---- contamination index: agent picks that the human had viewed,
    #      excluding tasks verdicted 'identical' (see PERSONALIZATION_PROTOCOL)
    human_viewed = set()
    hs_path = staging / "human_session.jsonl"
    if hs_path.exists():
        for line in hs_path.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") == "product_view" and d.get("asin"):
                human_viewed.add(d["asin"])
    overlap_tasks = [str(r.get("task_id", "")).strip() for r in agent
                     if r.get("asin", "").strip() in human_viewed
                     and verdicts.get(str(r.get("task_id", "")).strip())
                     != "identical"]
    denom = sum(1 for t in ("1", "2", "3") if verdicts.get(t) != "identical")
    contamination = {
        "overlapping_nonidentical_tasks": overlap_tasks,
        "index": (len(overlap_tasks) / denom) if denom else 0.0,
        "human_viewed_asin_count": len(human_viewed),
    }

    # ---- report + manifest + zip ----
    build_report(staging, student_id, verdicts,
                 picks_table(agent, human), screenshots)
    manifest = {
        "student_id": student_id,
        "packed_at_utc": datetime.now(timezone.utc).isoformat(),
        "deliverables": {
            "1_questionnaire": "persona_survey.csv|md",
            "2_purchase_history": "purchase_profile.md "
                                  "(agent-extracted from amazon.in orders; "
                                  "raw CSV only if research add-on used)",
            "3_tasks": "tasks.md",
            "4_agent_trace": f"decision_log.md + hermes_logs/ ({n_logs} files)",
            "5_agent_picks": "agent_picks.csv + screenshots/",
            "6_human_picks": "human_picks.csv + human_session.jsonl "
                             "(shopping-process clickstream)",
            "7_comparison": "comparison.md",
        },
        "arm": arm,
        "verdicts": verdicts,
        "human_process": {"searches": n_search, "product_views": n_views},
        "contamination_index": contamination,
        "validation_issues": issues,
        "sha256": {p.name: sha256(p) for p in sorted(staging.rglob("*"))
                   if p.is_file()},
    }
    (staging / "manifest.json").write_text(json.dumps(manifest, indent=2))

    out = HOME / "dtlab" / f"{student_id}_evidence.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(staging.rglob("*")):
            if p.is_file():
                z.write(p, f"{student_id}/{p.relative_to(staging)}")
    shutil.rmtree(staging)

    print(f"\nPacked -> {out}")
    if issues:
        print("VALIDATION ISSUES (fix and re-run dtlab-pack):")
        for i in issues:
            print(f"  [!!] {i}")
        return 1
    print("All 7 deliverables present and valid. Upload the zip to the LMS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
