#!/usr/bin/env bash
# setup.sh — container-adapted provisioning for the Codespaces route.
# Mirrors provisioning/provision.sh but for the devcontainer: Debian base
# (apt chromium works here; on Ubuntu VMs chromium is snap-packaged),
# desktop-lite provides the noVNC desktop on display :1 / web port 6080.
# Runs automatically on codespace creation (postCreateCommand).
set -euo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"   # repo root = the dt-lab kit

echo "== [1/5] Packages =="
sudo apt-get update
sudo apt-get install -y chromium ffmpeg jq unzip

echo "== [2/5] Playwright =="
pip install --user playwright
python3 -m playwright install chromium
sudo python3 -m playwright install-deps chromium || true

echo "== [3/5] Hermes Agent =="
# Official Nous Research installer (verify URL at term start; releases move fast)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

echo "== [4/5] Lab layout =="
mkdir -p "$HOME/dtlab/workspace" "$HOME/dtlab/evidence" "$HOME/dtlab/tools"
cp -v "$KIT/agent/SOUL.md"              "$HOME/dtlab/workspace/SOUL.md"
cp -v "$KIT/templates/tasks.md"         "$HOME/dtlab/workspace/tasks.md"
mkdir -p "$HOME/dtlab/human"
cp -v "$KIT/templates/human_picks.csv"  "$HOME/dtlab/human/human_picks.TEMPLATE.csv"
cp -v "$KIT/tools/log_human_session.py" "$HOME/dtlab/tools/"
cp -v "$KIT/templates/comparison.md"    "$HOME/dtlab/workspace/comparison.md"
cp -v "$KIT/data-pipeline/"*.py         "$HOME/dtlab/tools/"
cp -v "$KIT/questionnaire/make_persona.py" "$HOME/dtlab/tools/"
cp -v "$KIT/tools/pack_evidence.py"     "$HOME/dtlab/tools/"
cp -v "$KIT/provisioning/student_start.sh" "$HOME/dtlab/tools/"

echo "== [5/5] Commands =="
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/dtlab-start" <<'EOF'
#!/usr/bin/env bash
exec bash "$HOME/dtlab/tools/student_start.sh"
EOF
cat > "$HOME/.local/bin/dtlab-record" <<'EOF'
#!/usr/bin/env bash
OUT="$HOME/dtlab/evidence/run_$(date +%Y%m%d_%H%M%S).mkv"
echo "Recording desktop :1 to $OUT — Ctrl+C here to stop."
ffmpeg -f x11grab -framerate 12 -i "${DISPLAY:-:1}" -c:v libx264 \
       -preset veryfast -pix_fmt yuv420p "$OUT"
EOF
cat > "$HOME/.local/bin/dtlab-pack" <<'EOF'
#!/usr/bin/env bash
exec python3 "$HOME/dtlab/tools/pack_evidence.py" "$@"
EOF
cat > "$HOME/.local/bin/dtlab-shop" <<'EOF'
#!/usr/bin/env bash
exec python3 "$HOME/dtlab/tools/log_human_session.py" "$@"
EOF
chmod +x "$HOME/.local/bin/"dtlab-*
grep -q 'dtlab PATH' "$HOME/.bashrc" || cat >> "$HOME/.bashrc" <<'EOF'
# dtlab PATH
export PATH="$HOME/.local/bin:$PATH"
export DISPLAY="${DISPLAY:-:1}"
alias chromium-browser=chromium
EOF

echo ""
echo "Setup complete. Open the 'Lab Desktop' forwarded port (6080) in your"
echo "browser (password: dtlab), then use the VS Code terminal for:"
echo "  dtlab-start | dtlab-record | dtlab-pack"
