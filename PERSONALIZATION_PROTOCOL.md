# Personalization protocol — handling Amazon's memory of the account

Amazon personalizes what both the student and the agent see: "Previously
viewed", "Buy it again", "Inspired by your browsing history", re-ranked
search results. This splits into two very different issues. One is a
feature to keep; the other is a confound to control.

## Issue A — pre-existing account personalization: KEEP IT

The account's long-run personalization (built from years of purchases and
browsing) is part of the participant's *real choice environment*. Both the
human and the agent shop inside it, and the twin's job is precisely to
choose as this person would *in this person's world*. Sterilizing the
account (fresh account, incognito) would (a) destroy ecological validity,
(b) break the purchase-history grounding, and (c) be impossible to do
symmetrically anyway. So: pre-existing personalization stays, is identical
for both shoppers at baseline, and is documented as part of the design,
not a limitation.

## Issue B — within-experiment contamination: REDUCE, BLOCK, MEASURE

The real threat: the human shops first (by design), so the agent shops in
an environment freshly perturbed by the human's session — "previously
viewed" badges on the very items the human considered, browsing-history
carousels seeded with the human's candidates, short-term re-ranking toward
them. Left alone, this biases the agent *toward* the human's picks and
inflates every agreement metric. Known direction, unknown size — so we
attack it on three layers:

### Layer 1 — REDUCE at the source: PAUSE Browsing History (required)

Amazon has a purpose-built temporary switch — use the pause, not the
permanent toggle:

**Desktop:** amazon.in → Accounts & Lists → **Browsing History** → gear
icon (Manage history) → **Pause History → 1 day** → then **Remove all
items from view** to clear the existing trail.
**App:** profile icon → Browsing history (under "Keep shopping for") →
gear icon → **Pause History → 1 day**.

Pausing for 1 day on lab-day morning covers both sessions and
self-reverses — no cleanup step, nothing left permanently changed on 180
personal accounts. `dtlab-start` gates on a self-attested confirmation.
Two caveats for the handout: (a) users have reported the permanent on/off
toggle occasionally flipping back on by itself — the pause appears more
reliable, but students should verify the Browsing History page shows
paused/empty before proceeding; (b) even paused, this closes the
BROWSING-driven surfaces (the contamination channel); purchase-driven
surfaces like "Buy it again" remain, which is the baseline personalization
we deliberately keep (Issue A).

At setup (T-7, once, before ANY lab session):
1. amazon.in → Browsing History → **Manage history** → **Remove all items**
   → toggle **Turn Browsing History OFF**.
2. Verify the Browsing History page shows empty/off.

With browsing history off for BOTH sessions, the "previously viewed" /
"inspired by browsing" surfaces never populate from the human's session,
and the two shoppers face symmetric conditions. (Purchase-history-driven
surfaces like "Buy it again" remain — that's Issue A, wanted.)
(Gate implemented in `dtlab-start` as described above.) Note honestly: Amazon may still use short-term session signals
for ranking internally; the toggle removes the visible and strongest
channel, not necessarily every trace — hence Layers 2 and 3.

### Layer 2 — BLOCK on the agent side (SOUL rule)

The human must shop naturalistically, so we can't constrain them. The
agent we can constrain completely. SOUL.md now requires:
- Candidate sets built ONLY from fresh keyword searches the agent
  formulates itself from the persona and history files.
- Never open or use recommendation carousels or history-based surfaces
  ("Previously viewed", "Buy it again", "Inspired by...", "Customers who
  viewed...", homepage recommendations).
- If a search result visibly carries a "previously viewed"-type badge,
  note it in the decision log and evaluate the product on its merits only.
- Decision log records, per candidate, its source: `search#<rank>` — so
  candidate provenance is auditable.

This closes the main contamination pathway at the point where it would
enter the data.

### Layer 3 — MEASURE what remains (contamination index)

We already log everything needed to quantify residual contamination
instead of hand-waving it:
- Human side: the set of ASINs viewed in `human_session.jsonl`.
- Agent side: the candidates and picks in `decision_log.md` /
  `agent_picks.csv`.

`dtlab-pack` computes and writes into the manifest a **contamination
index**: the overlap between the agent's chosen ASINs and the human's
viewed set, excluding tasks verdicted `identical` (where convergence is
the finding, not contamination). At cohort level, regress agreement on
the index; report it in the paper. If the index is ~0 for non-identical
tasks, Layers 1–2 worked and the agreement numbers stand clean. If it
isn't, you have the covariate to control for — either way the experiment
survives review.

### Residual timing guidance

Prefer a gap of a few hours between `dtlab-shop` and the agent run
(e.g. human session in the morning, agent run in the afternoon lab)
— long enough for session-level ranking signals to decay, short enough
to keep the login warm for CAPTCHA purposes. Same day is fine; same
minute is not ideal.

## What to write in the methods section (pre-drafted honesty)

"Both shoppers operated within the participant's authentic, long-run
personalized account environment (ecological validity). Within-experiment
carry-over from the human session to the agent session was (i) attenuated
by disabling and clearing Amazon browsing history prior to all sessions,
(ii) structurally blocked on the agent side by restricting candidate
generation to de novo keyword search with recommendation surfaces
prohibited, and (iii) quantified per participant as the overlap between
agent selections and human-viewed items, which we report and control for."


## Layer 4 — RANDOMIZE the order (counterbalanced arms)

The strongest control: randomize students into two arms and estimate the
order effect instead of arguing about it.

- **H_FIRST** (human → agent): human uncontaminated; agent faces the
  human-perturbed account.
- **A_FIRST** (agent → human): agent uncontaminated; human faces the
  agent-perturbed account — **valid only with blinding** (below).

### The blinding requirement (what makes A_FIRST interpretable)

In A_FIRST, if the student watches their agent shop, their subsequent
"own" picks are directly contaminated by *observation* — a far larger
channel than platform carry-over, and it would poison the arm. Protocol:
A_FIRST students work in pairs. Both start their agents, then **swap
seats**: each babysits the *partner's* run (CAPTCHA-solving needs no
account knowledge; login happened before the swap). The babysitter — not
the owner — takes the cart screenshot and empties the cart. Owners see
nothing of their own agent's choices until after their own shopping is
done. Enforcement: the arm is recorded in `~/dtlab/arm.txt`, `dtlab-start`
enforces per-arm ordering, and `dtlab-pack` verifies file timestamps
against the run marker in the arm-appropriate direction and writes the
arm into the manifest.

### What the arm comparison can and cannot show (read before claiming)

1. The two arms do NOT carry the same contamination mechanism: H_FIRST
   has platform carry-over onto the agent; A_FIRST (blinded) has platform
   carry-over onto the human. "No difference between arms" therefore
   means "the NET order effect on outcomes is small," which — combined
   with Layer 1 (pause) and Layer 2 (agent search-only) closing the main
   channels — is strong evidence that carry-over does not drive the
   agreement results. It is not literally "zero contamination in both."
2. **A non-significant difference is not automatically evidence of
   absence.** Pre-specify an equivalence margin (e.g. ±10 percentage
   points on task-level agreement) and run an equivalence test (TOST) or
   report the confidence interval on the arm difference. With ~90
   participants × 3 tasks per arm you have reasonable power for margins
   in that range; a p>.05 from an underpowered comparison proves nothing
   and a reviewer will say so.
3. Randomize stratified (e.g. by section), record assignment centrally
   BEFORE session 2, and treat arm as a design factor in every analysis
   (it's in every manifest). Bonus: the contamination index should differ
   by arm in a predictable direction — a built-in manipulation check.
