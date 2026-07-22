#!/usr/bin/env bash
# provision.sh — Build the golden VM image for the Digital Twin lab.
# Run ONCE by the instructor on a clean Ubuntu 24.04 Desktop VM, then snapshot
# and export the VM (e.g. as .ova) for distribution. Students never run this.
#
# After provisioning, a student only needs to:
#   1. Import the VM, log in (student / <course password>)
#   2. Paste their Claude API key when prompted by student_start.sh
#   3. Drop persona_survey.md + purchase_history.csv into ~/dtlab/workspace
#   4. Run: dtlab-start
set -euo pipefail

echo "== [1/6] System packages =="
sudo apt-get update
sudo apt-get install -y git curl python3 python3-pip python3-venv \
    ffmpeg chromium-browser jq unzip

echo "== [2/6] uv + Playwright (for the capture scripts) =="
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv venv "$HOME/dtlab/.venv"
"$HOME/dtlab/.venv/bin/pip" install playwright
"$HOME/dtlab/.venv/bin/playwright" install chromium

echo "== [3/6] Hermes Agent =="
# Official Nous Research installer (verify URL against current docs at build time)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

echo "== [4/6] Lab directory layout =="
mkdir -p "$HOME/dtlab/workspace" "$HOME/dtlab/evidence" "$HOME/dtlab/tools"
# Kit files are expected alongside this script when building the image:
cp -v ../agent/SOUL.md              "$HOME/dtlab/workspace/SOUL.md"
cp -v ../data-pipeline/*.py         "$HOME/dtlab/tools/"
cp -v ../questionnaire/make_persona.py "$HOME/dtlab/tools/"
cp -v student_start.sh              "$HOME/dtlab/tools/"
cp -v ../tools/pack_evidence.py     "$HOME/dtlab/tools/"
# Templates land directly in the workspace; students fill them in place.
cp -v ../templates/tasks.md         "$HOME/dtlab/workspace/tasks.md"
mkdir -p "$HOME/dtlab/human"
cp -v ../templates/human_picks.csv  "$HOME/dtlab/human/human_picks.TEMPLATE.csv"  # manual fallback only
cp -v ../tools/log_human_session.py "$HOME/dtlab/tools/"
cp -v ../templates/comparison.md    "$HOME/dtlab/workspace/comparison.md"
chmod +x "$HOME/dtlab/tools/"*.sh

echo "== [5/6] Convenience commands =="
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/dtlab-start" <<'EOF'
#!/usr/bin/env bash
exec bash "$HOME/dtlab/tools/student_start.sh"
EOF
cat > "$HOME/.local/bin/dtlab-record" <<'EOF'
#!/usr/bin/env bash
# Screen-record the full desktop until Ctrl+C; saves to evidence folder.
OUT="$HOME/dtlab/evidence/run_$(date +%Y%m%d_%H%M%S).mkv"
echo "Recording to $OUT — press Ctrl+C in this terminal to stop."
ffmpeg -f x11grab -framerate 12 -i "$DISPLAY" -c:v libx264 -preset veryfast \
       -pix_fmt yuv420p "$OUT"
EOF
cat > "$HOME/.local/bin/dtlab-pack" <<'EOF2'
#!/usr/bin/env bash
exec python3 "$HOME/dtlab/tools/pack_evidence.py" "$@"
EOF2
cat > "$HOME/.local/bin/dtlab-shop" <<'EOF2'
#!/usr/bin/env bash
# Step that comes FIRST: your own logged shopping session + pick confirmation.
exec "$HOME/dtlab/.venv/bin/python" "$HOME/dtlab/tools/log_human_session.py" "$@"
EOF2
chmod +x "$HOME/.local/bin/dtlab-start" "$HOME/.local/bin/dtlab-record" \
         "$HOME/.local/bin/dtlab-pack" "$HOME/.local/bin/dtlab-shop"

echo "== [6/6] Done =="
echo "Now configure Hermes ONCE interactively so setup screens are cached:"
echo "  hermes setup    (choose Anthropic as provider; leave API key BLANK —"
echo "                   students insert their own via dtlab-start)"
echo "  enable browser automation in LOCAL browser mode (not cloud backends)"
echo "Then: clear shell history, remove any test keys, snapshot, export .ova."
