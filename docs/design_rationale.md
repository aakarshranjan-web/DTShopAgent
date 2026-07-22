# Design Rationale — Digital Twin Shopping Agent Lab

**What this document is.** The definitive record of every consequential
design decision in this package, with the argument for it and the
alternatives that were considered and rejected. It exists so that anyone
working on the kit (TA, co-instructor, future self, reviewer) understands
not just *what* the design is but *why it must be this way* — and which
parts are load-bearing versus merely convenient. Operational details live
in `COURSE_PLAN_1WEEK.md`; this file carries the reasoning.

**What the lab is.** ~180 MBA students each configure an autonomous agent
as their consumer digital twin (grounded in a 100-item questionnaire and
their real amazon.in purchase history), shop three standardized tasks both
themselves and via the agent under a counterbalanced order design, and
evaluate the agent's choices against their own. The exercise is
simultaneously a course module on agentic AI and a paired human/agent
choice-and-process experiment.

---

## 1. Agent framework: Hermes Agent

**Decision.** Hermes Agent (Nous Research, open-source, MIT) is the agent
runtime, driving a local Chromium browser over CDP via its built-in
browser tools.

**Why.** Four properties align exactly with the lab's needs. (1) A
customizable persistent identity file (`SOUL.md`) is the natural home for
the digital-twin directive, decision rules, mandatory logging protocol,
and hard boundaries — the entire experimental treatment is one readable
text file students can inspect, which is itself course content. (2)
Built-in browser automation that can attach to a *local, visible, already
logged-in* Chromium session: the student authenticates manually, then
hands the warm session to the agent. (3) Session transcripts are written
to local disk, giving an audit trail without any additional
instrumentation. (4) Self-hosted and open-source: no vendor account per
student, full inspectability, and pedagogical honesty — students see the
whole machine.

**Rejected.** *OpenClaw*: its architectural center of gravity is
multi-user, multi-platform chat gateway routing — capability the lab
doesn't use, complexity the lab pays for. *A purpose-built Playwright
script*: maximally controllable but it would be a scripted demo, not an
agent; the course is about agentic systems, and Hermes's autonomous
tool-use loop is the object of study. *Claude-native consumer agents
(e.g. browser-agent products)*: lower setup friction, but less
inspectable/configurable identity, less structured local logging, and the
course narrative is deliberately built on an open-source stack.

**Accepted risk.** Hermes releases fast; commands, config surfaces, and
log paths drift between versions. Mitigation: the docs-are-canonical
norm, a pinned dry run on the final environment before the course week,
and a TA work item to log every deviation.

## 2. Model backend: Claude API, one capped workspace

**Decision.** Claude (Sonnet-class) via API keys issued per student from
a single course workspace with a hard spend cap; keys generated
programmatically and revoked after the course.

**Why.** Agentic browser loops need a frontier-quality model to be
reliable enough for a *timed classroom session* — a failed run at minute
70 of a 3-hour session with 180 people has no retry slack. Sonnet-class
models deliver that reliability at a cost where a full three-task run is
well under $2; an $8/student cap covers retries, making total course cost
trivial against 15 contact hours. One workspace gives central kill-switch,
observability, and rate-limit management.

**Rejected.** *Local models (Ollama etc.)*: "free" is illusory here — on
CPU-only cloud containers or student laptops, small local models are too
slow and too error-prone for multi-step browser control; the failure mode
is silent classroom chaos. Retained only as an optional "hard mode"
footnote. *Students' own API accounts*: unbillable, unsupportable, and
uncapped at N=180.

## 3. Infrastructure: GitHub Codespaces on free personal accounts

**Decision.** The environment is a devcontainer at the repo root:
students create a plain (free) GitHub account, open the template repo,
click *Create codespace*, and get a bit-identical Linux desktop (noVNC in
a browser tab) with Hermes, Chromium, and all lab tooling pre-provisioned.

**Why.** Three constraints dominate at N=180 in one week: identical
environments, near-zero per-student setup, and zero dependence on
heterogeneous student hardware. Codespaces is the only free option that
satisfies all three. Every free personal GitHub account includes 120
core-hours/month (≈60 h runtime on the 2-core machine the config
requests) against a lab consuming ~8–10 h — no Student Pack, no
verification latency, no GitHub Classroom dependency. Setup is "create an
account, click a link, wait four minutes," which fits inside Session 1
with a triage buffer.

**Rejected.** *Local VMs (VirtualBox/UTM golden images)*: the earlier
primary route. Sound at small N with lead time, it collapses under 180
students × heterogeneous laptops × one week: two CPU architectures, BIOS
virtualization toggles, Hyper-V conflicts, RAM-starved hosts — a
hypervisor help desk the course cannot staff. Retained in
`provisioning/` (with host-check scripts and a triage table) strictly as
a fallback. *GitHub Classroom*: adds an organizational dependency for a
billing benefit the free personal quota already covers. *Oracle Cloud
Always Free*: generous specs but per-student account signup with card
verification and capacity lotteries — not classroom-reliable.
*Instructor-hosted cloud fleet*: most controlled, but makes the
instructor a sysadmin for the week; kept as plan C.

**Accepted risk — the one honest cost.** Codespaces egress from Azure
datacenter IPs, which Amazon's anti-bot systems treat with more suspicion
than residential IPs: more login OTPs, more mid-run CAPTCHAs. Three
compensations: the human-first session-warming effect (§6), the SOUL
rule that the agent halts at every CAPTCHA for human handling, and a
mandatory instructor dry run from a codespace against real amazon.in
*before the course week* that decides Codespaces-vs-fallback empirically
rather than on day 3. Deliberately out of scope: stealth/anti-detection
tooling — wrong lesson in a course about responsible agentic AI, and
unnecessary given the mitigations.

## 4. Purchase history: the agent reads it itself

**Decision.** There is no data-extraction pipeline in the student flow.
The agent's mandatory Bootstrap step (in `SOUL.md`) is: in the already
logged-in browser, open *Your Orders*, review roughly the last 12 months
under a hard effort cap (~30 orders / ~8 minutes), and write
`purchase_profile.md` — categories and frequencies, repeat brands, price
points, conspicuous absences, inferred decision style — with the rule
that **every claim must be traceable to an order actually seen**. That
file then serves as the revealed-preference ground truth for all tasks
and as deliverable #2.

**Why.** The alternative was a three-script pipeline (official
Privacy-Central export cleaner, Playwright scraper fallback, brand
enrichment) hanging off Amazon's export SLA of hours-to-weeks — a T−14
lead time that a one-week course simply does not have, plus DOM-fragile
code needing per-term validation. Letting the agent read the history
itself deletes all of it, requires zero student effort, and is
pedagogically superior: watching your agent walk your order history and
write down who it thinks you are is the most instructive three minutes of
the course. The traceability rule imports reference-verification
discipline into the agent's self-briefing and makes confabulated
"history" auditable against the session transcript.

**Trade-off, honestly priced.** Agent-read history is less precise than
the official export (no guaranteed completeness, no exact unit
economics). Accepted because the profile's role is preference grounding,
not accounting — and the precise path survives as an optional
*post-course* research add-on (`data-pipeline/`) for a consenting
validation subsample, where the export's latency no longer matters.

## 5. The questionnaire: instructor-authored, code-addressed, pipeline-enforced

**Decision.** The instructor supplies the ~100 items in a fixed CSV
contract (`item_code, construct, question, response_type, options,
constraint`). An Apps Script builds the Google Form from that CSV;
responses land in one Sheet (one row per student = the cohort persona
dataset); a batch tool generates per-student persona files overnight.
Item codes are the load-bearing element: they appear in Form headers,
survive into the persona file, and `SOUL.md` obliges the agent to cite
them verbatim in its decision log.

**Why each piece.** *Instructor-authored*: instrument design is the
professor's scientific contribution; the kit ships enforcing placeholders
(all downstream tools hard-fail until real items exist) so a draft can
never silently reach students. *Form-from-CSV rather than a shared
sheet*: forced responses, validated pseudonym IDs, one-submission-per-
person, and zero transcription between collection and dataset. *Codes as
citation vocabulary*: they make the agent's reasoning machine-auditable —
every rejection and selection must point at a specific item or the
purchase profile, enabling the citation-fidelity analysis (are the
agent's cited profile facts real or invented?) that connects this lab to
the broader GenAI-quality-assurance research agenda. *The `constraint`
flag*: inviolable rules (allergies, dietary/religious exclusions, hard
budget rules) travel as data, so "constraints always win" holds under any
coding scheme without hard-coding a single item anywhere.

## 6. Order of shopping: counterbalanced arms with enforced blinding

**Decision.** Students are randomized (stratified, pre-assigned) into two
arms. **H_FIRST**: the student shops the three tasks first in an
instrumented browser (`dtlab-shop`, clickstream logged), confirms picks,
then the agent runs. **A_FIRST**: the agent runs first — *babysat by a
partner, not the owner* — then the student shops, blinded to the agent's
output until their own picks are committed. Human-side artifacts live in
`~/dtlab/human/`, which the agent is barred from reading; ordering and
quarantine are enforced by pre-flight checks and by timestamp validation
at packing, with the arm recorded in every manifest.

**Why the structure.** Whoever goes second is exposed to the other's
influence through two distinct channels: *observation* (seeing the other
shopper's process/choices) and *platform carry-over* (Amazon's session-
level personalization perturbed by the first shopper). Observation is the
larger channel and is fully closable: H_FIRST closes it for the human by
construction; A_FIRST closes it via partner-babysitting (CAPTCHA-solving
needs no account knowledge; the babysitter screenshots and empties the
cart). What remains in each arm is platform carry-over — onto the agent
in H_FIRST, onto the human in A_FIRST — which is exactly what the
randomization estimates (§7). Enforcement is mechanical, not trusted:
`dtlab-start` refuses out-of-order launches, the packer rejects
timestamp-inconsistent submissions and quarantine leaks, and all of it is
regression-tested (`tests/simulate_submission.sh`).

**Why the human's process is logged at all.** `dtlab-shop` passively
captures searches, product views, cart clicks, and filter changes
(explicitly excluding keystrokes, non-Amazon browsing, and
checkout/payment/auth paths). This upgrades the study from outcome
comparison to **process comparison** — consideration-set size and
overlap, query formulation, search depth, sponsored exposure, human vs.
agent — arguably the design's most novel contribution, and it costs the
student nothing: pick confirmation at session end auto-generates their
picks file.

## 7. Personalization and contamination: keep, reduce, block, measure, randomize

**Decision.** Amazon's *long-run* account personalization is deliberately
kept; *within-experiment* carry-over is handled by four layers.

**Keep the baseline (the part that is a feature).** The account's
history-shaped environment is the participant's real choice context.
Both shoppers face it identically at baseline; the twin's task is to
choose as this person would *in this person's world*. Sterilizing it
(fresh accounts, incognito) would destroy ecological validity and the
history grounding simultaneously.

**Layer 1 — reduce:** on lab-day morning, students **pause Browsing
History for 1 day** (Browsing History → gear → Pause History) and remove
existing items from view. The pause, unlike the permanent toggle, is
purpose-built for temporary use and self-reverses — nothing left changed
on 180 personal accounts. It closes the browsing-driven surfaces
("previously viewed", "inspired by your browsing"), which are the
contamination channel, while purchase-driven surfaces remain (baseline,
wanted). Honest limits: enforcement is a self-attested gate in
`dtlab-start` (the ceiling of verifiability at scale), and pausing kills
the visible channel, not provably every internal session signal — hence
the layers below.

**Layer 2 — block (agent side):** the human must shop naturalistically
and cannot be constrained; the agent can be constrained completely.
`SOUL.md` restricts candidate generation to de-novo keyword searches the
agent formulates itself; recommendation carousels and history-based
surfaces are prohibited; every candidate's provenance is logged as
`search#<rank>`, making compliance auditable from the trace.

**Layer 3 — measure:** the packer computes a per-participant
**contamination index** into the manifest — overlap between agent picks
and human-viewed ASINs, excluding tasks verdicted `identical` (where
convergence is the finding). Residual carry-over becomes a covariate,
not a hand-wave; and it should differ between arms in a predictable
direction, providing a built-in manipulation check.

**Layer 4 — randomize:** the arm design (§6) turns order effects into an
estimable quantity. Statistical commitment, stated in advance: "no
significant arm difference" is *not* automatically evidence of absence.
The analysis pre-registers an equivalence margin (e.g. ±10 pp on
task-level agreement) and uses an equivalence test (TOST) or reports the
CI on the arm difference — with ~90 participants × 3 tasks per arm,
adequately powered for margins in that range. The defensible claim is:
net order effects on outcomes are bounded below the margin, with the two
dominant channels independently closed by Layers 1–2 and residuals
measured by Layer 3.

## 8. Tasks, verdict scale, and deliverables

**Three standardized task frames** (replenishment ≤ ₹600; considered
purchase ₹1,000–3,000; gift ≤ ₹1,500 for a student-described recipient)
so results aggregate across the cohort. The gift task is deliberately the
hardest: it tests whether the twin modeled the student's *social* self,
and the questionnaire can include a matching stated-preference item as a
direct benchmark.

**Verdict scale: `better | identical | equivalent | inferior`** (agent's
choice relative to the student's own). Superior to a naive
better/worse/equal because it separates *exact product convergence*
(identical) from *functional substitution* (equivalent) — two different
levels of twin fidelity. And `identical` is not self-reported: the packer
cross-checks every verdict against the two picks files' ASINs, rejecting
`identical` on differing ASINs and any other verdict on matching ones —
turning one category into an objective, verified measurement.

**Seven deliverables, one validated file.** Questionnaire (persona
files), purchase profile (agent-written), the tasks as given, the full
agent trace (decision log + auto-collected Hermes session transcripts
since the run marker), agent picks (structured CSV + cart screenshot),
human picks + shopping clickstream, and the comparison with parsed
verdict lines. `dtlab-pack` validates all of it (row counts, real ASINs,
verdict–ASIN consistency, quarantine, arm-consistent ordering, no
leftover placeholders), writes SHA-256 hashes and the arm into
`manifest.json`, renders a self-contained `report.html` for graders, and
emits one zip. Invalid packs still produce the zip but exit non-zero with
an explicit fix list — a student cannot silently submit an incomplete
pack, and the instructor cannot receive one without knowing what's
missing. Cohort assembly then reduces mostly to concatenating CSVs; only
citation-fidelity coding touches free text.

**Why no browser plugin for logging.** An earlier idea. Rejected because
the three-layer trail already in hand — Hermes session transcripts, the
mandated agent-written decision log, and screen recording — covers the
agent side redundantly, and `dtlab-shop`'s Playwright instrumentation
covers the human side, all inside one codebase with no extension
distribution, no developer-mode installs, and no third browser-permission
conversation with 180 students.

## 9. Safety, ethics, and account risk

**Hard boundaries, in the agent's identity file:** add-to-cart only;
never checkout, addresses, payments, account settings, or subscriptions;
order-history pages are the only account pages it may open; halt at every
CAPTCHA. Students remove saved payment methods from the lab browser
profile; carts are emptied after evidence capture.

**Research ethics:** course participation and research participation are
separable — consent covers the pseudonymized questionnaire, the
purchase-profile extract, the clickstream (with its explicit exclusions),
and agent logs; a synthetic-persona pack provides a no-questions opt-out
with no grade impact; pseudonym↔name mapping is held separately by the
instructor and destroyed post-study; data minimization is implemented in
code (the pre-flight refuses to launch with PII-shaped files in the
workspace) rather than promised in prose. Ethics/IRB approval precedes
the questionnaire.

**Account risk, stated plainly in the syllabus:** automated interaction
sits in tension with Amazon's conditions of use. Mitigations — manual
login, human-warmed sessions, human-paced actions, add-to-cart only, one
short run — reduce but do not eliminate the risk of an account being
flagged; the synthetic-persona path doubles as the zero-risk option, and
class time is never spent fighting Amazon (pre-decided fallbacks in the
course plan).

## 10. Timeline: why 2 × 3 h + one overnight works

Session 1 is environment + identity (account, codespace, key, smoke test,
task setup) with a long triage buffer — at N=180, ~10–15 stuck
environments are a planning assumption, not a surprise. The questionnaire
runs overnight; the instructor's batch tool turns the response sheet into
per-student persona files in minutes and prints a completion roster for
chasing stragglers. Session 2 runs both arms in mirrored phases (shop /
agent for one half; agent-babysat / shop-blinded for the other), then
individual comparison writing, one-command packing, and a live verdict
poll split by arm — the class watches its own order-effect estimate
materialize. Everything cut from earlier drafts (data-export lead times,
VM funnels, host checks as a student-facing step) was cut because it
could not survive this clock; everything retained is either enforced in
code or has a pre-decided classroom fallback.

## 11. Known limitations, accepted deliberately

1. **DOM fragility** in the human-session logger (cart-click selector,
   URL parsing) — single patch points, TA-validated against live
   amazon.in shortly before the course.
2. **Hermes release drift** — docs canonical, dry run decisive.
3. **Datacenter-IP CAPTCHA friction** — measured in the dry run, with
   the fallback decision made before, not during, the week.
4. **Agent-read history is imprecise** relative to the official export —
   acceptable for preference grounding; precise path available
   post-course for a validation subsample.
5. **Layer-1 pause is self-attested** and closes the visible channel
   only — which is exactly why Layers 2–4 exist and carry the
   inferential weight.
6. **Empty-history students** produce persona-only twins — flagged, kept,
   and analyzed as a natural comparison subgroup rather than excluded.

The unifying design principle behind all of the above: **every claim the
experiment will need to defend is either enforced by code or measured as
data — never merely instructed.** Ordering, blinding, quarantine, verdict
consistency, citation traceability, and contamination are all in that
category; where enforcement is impossible (the pause, naturalistic human
shopping), the design measures instead. That principle is what makes a
classroom exercise with 180 MBA students simultaneously a publishable
paired-choice experiment.
