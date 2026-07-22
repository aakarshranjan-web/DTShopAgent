#!/usr/bin/env bash
# student_start.sh — the ONLY command students need. Validates everything,
# collects the API key on first run, and walks through the session.
set -uo pipefail
WS="$HOME/dtlab/workspace"
# Set this to the final item count of the course questionnaire (see
# questionnaire/AUTHORING_GUIDE.md). Used for the completeness check only.
EXPECTED_ITEMS=100
GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  [ok]${NC} $1"; }
bad()  { echo -e "${RED}  [!!]${NC} $1"; FAIL=1; }
note() { echo -e "${YEL}  [..]${NC} $1"; }
FAIL=0

echo "=============================================="
echo " Digital Twin Lab — pre-flight check"
echo "=============================================="

# 1. Claude API key (stored in Hermes env config on first run)
if [ -z "${ANTHROPIC_API_KEY:-}" ] && ! grep -qs "ANTHROPIC_API_KEY" \
     "$HOME/.hermes/"* 2>/dev/null; then
  echo ""
  read -rp "Paste your course-issued Claude API key (sk-ant-...): " KEY
  if [[ "$KEY" == sk-ant-* ]]; then
    mkdir -p "$HOME/.hermes"
    # export for this session; hermes setup persists it in its own config
    export ANTHROPIC_API_KEY="$KEY"
    echo "export ANTHROPIC_API_KEY=$KEY" >> "$HOME/.bashrc"
    ok "API key stored for this VM (course workspace, hard spend cap)."
  else
    bad "That does not look like a Claude API key. Re-run dtlab-start."
  fi
else
  ok "Claude API key present."
fi

# 2. Required workspace files
[ -f "$WS/SOUL.md" ] && ok "SOUL.md (agent identity) present" \
                     || bad "SOUL.md missing from $WS"
[ -f "$WS/tasks.md" ] && ! grep -q "INSTRUCTOR_TASK" "$WS/tasks.md" \
  && ok "tasks.md present and filled" \
  || bad "tasks.md missing or still contains template placeholders"
HU="$HOME/dtlab/human"
ARMFILE="$HOME/dtlab/arm.txt"
if [ ! -f "$ARMFILE" ]; then
  echo ""
  read -rp "Your assigned experimental arm (from the instructor list) [H_FIRST/A_FIRST]: " ARM
  case "$ARM" in
    H_FIRST|A_FIRST) echo "$ARM" > "$ARMFILE" ;;
    *) echo -e "${RED}Enter exactly H_FIRST or A_FIRST (check the LMS assignment sheet).${NC}"; exit 1 ;;
  esac
fi
ARM=$(cat "$ARMFILE")
ok "experimental arm: $ARM"
if [ "$ARM" = "H_FIRST" ]; then
  if [ -f "$HU/human_picks.csv" ] && [ -f "$HU/human_session.jsonl" ]; then
    ok "H_FIRST order respected: your shopping is done, agent goes second"
  else
    bad "H_FIRST arm: run  dtlab-shop  BEFORE the agent"
  fi
else
  if [ -f "$HU/human_picks.csv" ] || [ -f "$HU/human_session.jsonl" ]; then
    bad "A_FIRST arm: human files already exist — the agent must run FIRST in your arm; if you shopped by mistake, tell a TA (arm reassignment beats fake ordering)"
  else
    ok "A_FIRST order respected: agent runs first; you shop AFTER (blinded — your partner babysits this run, you do not watch)"
  fi
fi
[ -f "$WS/human_picks.csv" ] \
  && bad "human_picks.csv found in the AGENT workspace — move it to ~/dtlab/human/ (the agent must not see your picks)"
if [ -f "$WS/persona_survey.md" ]; then
  N=$(grep -c '^\- \*\*' "$WS/persona_survey.md" || true)
  MIN=$(( EXPECTED_ITEMS * 95 / 100 ))
  if [ "$N" -ge "$MIN" ]; then
    ok "persona_survey.md present ($N/$EXPECTED_ITEMS items)"
  elif [ "$N" -gt 0 ]; then
    bad "persona_survey.md has only $N/$EXPECTED_ITEMS items — regenerate"
  else
    bad "persona_survey.md is empty or malformed — regenerate"
  fi
else
  bad "persona_survey.md missing — run make_persona.py first (see handout §6)"
fi
note "purchase profile: created BY THE AGENT from your amazon.in order
       history as its first action (no extraction needed beforehand)"

# 3. Forbidden files (privacy check — these must NOT be in the workspace)
for f in "$WS"/*address* "$WS"/*payment* "$WS"/Retail.OrderHistory*; do
  [ -e "$f" ] && bad "Remove raw/PII file from workspace: $f"
done

if [ "$FAIL" -ne 0 ]; then
  echo ""
  echo -e "${RED}Fix the [!!] items above, then run dtlab-start again.${NC}"
  exit 1
fi

echo ""
echo "All checks passed. Session order:"
echo "  1. In ANOTHER terminal:   dtlab-record        (starts screen capture)"
echo "  2. Chromium opens next -> log into amazon.in MANUALLY, empty the cart."
echo "  3. Hermes CLI starts    -> run: /browser connect"
echo "  4. Paste the standardized task prompt from the handout."
echo "  5. Watch. Intervene ONLY for CAPTCHAs (note every intervention)."
echo "  6. Afterwards: screenshot the cart, then EMPTY it."
echo "  7. Evidence auto-collects from ~/dtlab/workspace + evidence folder."
echo ""
read -rp "Amazon Browsing History PAUSED for 1 day (Browsing History > gear icon > Pause History) and existing items removed from view? [y/N] " BH
case "$BH" in
  [yY]*) ok "browsing history paused — browsing-driven carry-over channel closed for both sessions" ;;
  *) echo -e "${RED}Do that now (takes 30 seconds; exact steps in PERSONALIZATION_PROTOCOL.md), then re-run dtlab-start.${NC}"; exit 1 ;;
esac
read -rp "Press Enter to open the browser and start Hermes... "
touch "$HOME/dtlab/.run_started"   # marker: pack_evidence.py collects Hermes logs from here on
echo "(After the run + comparison memo: run  dtlab-pack  to build your single submission zip.)"
chromium-browser "https://www.amazon.in" >/dev/null 2>&1 &
sleep 2
cd "$WS" && exec hermes
