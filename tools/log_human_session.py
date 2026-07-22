#!/usr/bin/env python3
"""
log_human_session.py — instrument the STUDENT'S OWN shopping session.

Runs BEFORE the agent ever starts. Opens the same persistent browser profile
the agent will later use (this is deliberate: a session warmed by genuine
human shopping is the best anti-bot mitigation available), and passively logs
the student's shopping process while they complete the three tasks
themselves, exactly as they normally would.

CAPTURED (to ~/dtlab/human/human_session.jsonl, schema dtlab-humanlog-v1):
  search        — query text, results page number
  product_view  — ASIN, page title, dwell start
  cart_add      — click on Add-to-Cart / Buy-Now (injected listener)
  filter_sort   — sort/filter changes visible in the URL
  nav           — any other amazon.in navigation (fallback)

NOT captured: keystrokes, non-amazon sites, passwords, payment pages
(the /gp/buy and /checkout paths are explicitly dropped).

At the end the script walks the student through confirming their final pick
per task (offering the products they viewed) and writes human_picks.csv.

EVERYTHING is written to ~/dtlab/human/ — a directory the agent is barred
from reading (SOUL.md hard boundary + pre-flight check), so the agent's run
cannot be contaminated by the human's choices.

USAGE
  python3 log_human_session.py --student-id DT2026-042
  ...shop normally in the opened browser; empty the cart when done...
  ...return to the terminal, press Enter, confirm your 3 picks...
"""

import argparse
import csv
import json
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright

HUMAN_DIR = Path.home() / "dtlab" / "human"
PROFILE = Path.home() / ".dtlab-browser-profile"   # same profile agent uses
ASIN_RE = re.compile(r"(?:/dp/|/gp/product/)([A-Z0-9]{10})")
BLOCK_PATHS = ("/gp/buy", "/checkout", "/payments", "/ap/")  # never log these
SCHEMA = "dtlab-humanlog-v1"

CART_LISTENER_JS = """
document.addEventListener('click', (e) => {
  const el = e.target.closest(
    '#add-to-cart-button, #buy-now-button, input[name="submit.add-to-cart"],' +
    ' [data-action="add-to-cart"], #add-to-cart-button-ubb');
  if (el && window.dtlabEvent) {
    window.dtlabEvent(JSON.stringify(
      {type: 'cart_add', url: location.href, title: document.title}));
  }
}, true);
"""


class Logger:
    def __init__(self, out_path, student_id):
        self.f = open(out_path, "a", encoding="utf-8")
        self.lock = threading.Lock()
        self.student_id = student_id
        self.viewed = {}   # asin -> latest title (for pick confirmation)

    def emit(self, type_, **kw):
        rec = {"ts": datetime.now(timezone.utc).isoformat(),
               "student_id": self.student_id, "type": type_, **kw}
        with self.lock:
            self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.f.flush()

    def on_nav(self, url, title=""):
        u = urlparse(url)
        if "amazon.in" not in u.netloc:
            return                       # never log non-amazon browsing
        if any(u.path.startswith(b) for b in BLOCK_PATHS):
            return                       # never log checkout/payment/auth
        q = parse_qs(u.query)
        m = ASIN_RE.search(u.path)
        if m:
            asin = m.group(1)
            t = re.sub(r"\s*[-|].*?Amazon\.in.*$", "", title).strip()
            self.viewed[asin] = t or self.viewed.get(asin, "")
            self.emit("product_view", asin=asin, title=t, url=u.path)
        elif u.path == "/s" and "k" in q:
            self.emit("search", query=q["k"][0],
                      page=q.get("page", ["1"])[0],
                      sort=q.get("s", [""])[0])
        elif "rh" in q or "s" in q:
            self.emit("filter_sort", url=u.path + "?" + u.query[:200])
        else:
            self.emit("nav", url=u.path)

    def on_binding(self, source, payload):
        try:
            d = json.loads(payload)
        except json.JSONDecodeError:
            return
        m = ASIN_RE.search(d.get("url", ""))
        self.emit("cart_add", asin=m.group(1) if m else "",
                  title=re.sub(r"\s*[-|].*?Amazon\.in.*$", "",
                               d.get("title", "")).strip())


def confirm_picks(log: Logger, student_id):
    """Interactive confirmation of the final pick per task -> human_picks.csv."""
    recent = list(log.viewed.items())[-15:]
    print("\nProducts you viewed this session:")
    for i, (asin, title) in enumerate(recent, 1):
        print(f"  [{i:2d}] {asin}  {title[:70]}")
    rows = []
    for task in ("1", "2", "3"):
        print(f"\n--- Task {task}: your final pick ---")
        sel = input("Number from the list above, or paste an ASIN: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(recent):
            asin, title = recent[int(sel) - 1]
        else:
            asin, title = sel.upper(), log.viewed.get(sel.upper(), "")
            if not re.fullmatch(r"[A-Z0-9]{10}", asin):
                print("  (that doesn't look like an ASIN — recorded as-is,"
                      " fix in human_picks.csv if needed)")
            if not title:
                title = input("  Product title: ").strip()
        price = input("  Price in Rs. (number only): ").strip()
        why = input("  Why this one (2-3 sentences): ").strip()
        rows.append({"task_id": task, "title": title, "asin": asin,
                     "url": f"https://www.amazon.in/dp/{asin}",
                     "price_inr": price, "reasoning": why})
    out = HUMAN_DIR / "human_picks.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["task_id", "title", "asin", "url",
                                          "price_inr", "reasoning"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student-id", required=True)
    args = ap.parse_args()
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    log = Logger(HUMAN_DIR / "human_session.jsonl", args.student_id)
    log.emit("session_start", schema=SCHEMA)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE), headless=False,
            viewport={"width": 1280, "height": 900})
        ctx.expose_binding("dtlabEvent", log.on_binding)
        ctx.add_init_script(CART_LISTENER_JS)

        def wire(page):
            page.on("load",
                    lambda: log.on_nav(page.url, page.title()))
        for pg in ctx.pages:
            wire(pg)
        ctx.on("page", wire)

        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.amazon.in")
        print("\n>>> Shop for your THREE tasks yourself, exactly as you")
        print(">>> normally would. Log in if needed. Take your time.")
        print(">>> When finished (and cart EMPTIED), return here and")
        input(">>> press Enter... ")
        try:
            ctx.close()
        except Exception:
            pass

    log.emit("session_end")
    confirm_picks(log, args.student_id)
    print("\nDone. Next step: dtlab-start (the agent run).")
    print("Your picks live in ~/dtlab/human/ — the agent cannot read them.")


if __name__ == "__main__":
    sys.exit(main())
