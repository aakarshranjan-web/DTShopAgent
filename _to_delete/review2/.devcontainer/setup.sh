#!/usr/bin/env bash
# setup.sh — container-adapted provisioning for the Codespaces route
# (PRIMARY route, see COURSE_PLAN_1WEEK.md). Mirrors provisioning/provision.sh
# but for the devcontainer: Debian base (apt chromium works here; on Ubuntu
# VMs chromium is snap-packaged), desktop-lite provides the noVNC desktop on
# display :1 / web port 6080. Runs automatically on codespace creation
# (postCreateCommand) and must stay safe to re-run.
set -euo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"   # repo root = the dt-lab kit

# ---- pinned downloads -------------------------------------------------
# Remote installers are downloaded to a file, checksum-verified, then
# executed. "UNPINNED" FAILS the build until the TA pins a release
# (procedure: TA_ONBOARDING.md > "Updating installer pins") — with
# Codespaces prebuilds enabled, all 161 students then share one frozen,
# pre-tested image. TODO(dry-run): pin real version + checksum.
HERMES_INSTALLER_URL="https://hermes-agent.nousresearch.com/install.sh"
HERMES_INSTALLER_SHA256="UNPINNED"
PLAYWRIGHT_PIN=""   # e.g. "==1.55.0"; empty = latest (pin at dry run)

fetch_verified() {  # url sha256 dest
  local url="$1" sha="$2" dest="$3"
  if [ "$sha" = "UNPINNED" ] && [ "${DTLAB_ALLOW_UNPINNED:-0}" != "1" ]; then
    echo "ERROR: $url has no pinned SHA-256."
    echo "Pin it first (TA_ONBOARDING.md > Updating installer pins), or"
    echo "export DTLAB_ALLOW_UNPINNED=1 for a throwaway test build."
    exit 1
  fi
  curl -fsSL "$url" -o "$dest"
  if [ "$sha" != "UNPINNED" ]; then
    echo "$sha  $dest" | sha256sum -c - || {
      echo "ERROR: checksum mismatch for $url — a new release or tampering."
      echo "Do NOT bypass; re-pin per TA_ONBOARDING.md and re-run."
      exit 1
    }
  else
    echo "WARNING: running UNPINNED installer from $url (test build only)."
  fi
}

echo "== [1/7] Packages =="
sudo apt-get update
sudo apt-get install -y chromium ffmpeg jq unzip
pip install --user "playwright$PLAYWRIGHT_PIN"
python3 -m playwright install chromium
sudo python3 -m playwright install-deps chromium || true

echo "== [2/7] Hermes Agent =="
fetch_verified "$HERMES_INSTALLER_URL" "$HERMES_INSTALLER_SHA256" \
    /tmp/hermes-install.sh
bash /tmp/hermes-install.sh && rm -f /tmp/hermes-install.sh

echo "== [3/7] Lab layout =="
mkdir -p "$HOME/dtlab/workspace" "$HOME/dtlab/evidence" "$HOME/dtlab/tools"
cp -v "$KIT/agent/SOUL.md"                 "$HOME/dtlab/workspace/SOUL.md"
# kit-owned SOUL variants for the optional ablation factor (dtlab-start
# swaps the workspace SOUL.md per condition when the factor is enabled)
mkdir -p "$HOME/dtlab/soul"
cp -v "$KIT/agent/SOUL.md" "$KIT/agent/SOUL_ablated.md" \
      "$KIT/agent/SOUL_sandbox.md" "$HOME/dtlab/soul/"
cp -v "$KIT/templates/comparison_ablation.md" \
      "$HOME/dtlab/comparison_ablation.TEMPLATE.md"
cp -v "$KIT/dtlab_config.env"              "$HOME/dtlab/dtlab_config.env"
cp -v "$KIT/tasks_config.csv"              "$HOME/dtlab/tasks_config.csv"
mkdir -p "$HOME/dtlab/assets"
cp -v "$KIT/assets/ringelai.png"           "$HOME/dtlab/assets/" 2>/dev/null || true
cp -v "$KIT/tools/log_human_session.py"    "$HOME/dtlab/tools/"
cp -v "$KIT/tools/capture_cart.py"         "$HOME/dtlab/tools/"
cp -v "$KIT/tools/capture_verdicts.py"     "$HOME/dtlab/tools/"
cp -v "$KIT/tools/dtlab_browser.sh"        "$HOME/dtlab/tools/"
cp -v "$KIT/data-pipeline/"*.py            "$HOME/dtlab/tools/"
cp -v "$KIT/questionnaire/make_persona.py" "$HOME/dtlab/tools/"
cp -v "$KIT/tools/pack_evidence.py"        "$HOME/dtlab/tools/"
cp -v "$KIT/provisioning/student_start.sh" "$HOME/dtlab/tools/"
# Templates land in the workspace ONCE; students fill them in place, so a
# container rebuild must never clobber them.
[ -f "$HOME/dtlab/workspace/tasks.md" ] || \
  cp -v "$KIT/templates/tasks.md"          "$HOME/dtlab/workspace/tasks.md"
[ -f "$HOME/dtlab/workspace/comparison.md" ] || \
  cp -v "$KIT/templates/comparison.md"     "$HOME/dtlab/workspace/comparison.md"
mkdir -p "$HOME/dtlab/human"
cp -v "$KIT/templates/human_picks.csv" \
      "$HOME/dtlab/human/human_picks.TEMPLATE.csv"
find "$HOME/dtlab/tools" -name '*.sh' -exec chmod +x {} +

echo "== [4/7] Kit version stamp (reproducibility metadata) =="
printf 'commit=%s built=%s route=codespaces image=%s\n' \
  "$(git -C "$KIT" rev-parse --short HEAD 2>/dev/null || echo unknown)" \
  "$(date -u +%Y-%m-%dT%H:%MZ)" \
  "mcr.microsoft.com/devcontainers/python:1-3.12-bookworm" \
  > "$HOME/dtlab/kit_version.txt"

echo "== [5/7] Desktop password (per-codespace, replaces the shipped default) =="
# The desktop-lite feature bakes a fixed password at build time; rotate it
# to a per-codespace random one so a leaked/public port is not an open door.
NEWPW="$(tr -dc 'a-z0-9' < /dev/urandom | head -c 10 || true)"
ROTATED=0
if [ -n "$NEWPW" ]; then
  for f in /usr/local/share/desktop-init.sh /usr/local/etc/desktop-init.sh; do
    if [ -f "$f" ] && sudo grep -q 'dtlab' "$f"; then
      sudo sed -i "/passw/s/dtlab/$NEWPW/g" "$f" && ROTATED=1
    fi
  done
fi
if [ "$ROTATED" = "1" ]; then
  sudo pkill x11vnc 2>/dev/null || true   # supervisor restarts it with the new password
  echo "*** Your personal Lab Desktop password (write it down): $NEWPW ***"
else
  # TODO(dry-run): locate the desktop-lite password store in the built image
  # and make the rotation stick; until verified, the default applies.
  echo "WARNING: could not rotate the desktop password automatically —"
  echo "the shipped default 'dtlab' is in effect."
fi
echo ""
echo "*** NEVER set the forwarded port 6080 to Public. A public port gives"
echo "*** anyone with the URL a desktop logged into YOUR Amazon account."

echo "== [6/7] Commands =="
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/dtlab-start" <<'EOF'
#!/usr/bin/env bash
exec bash "$HOME/dtlab/tools/student_start.sh"
EOF
cat > "$HOME/.local/bin/dtlab-record" <<'EOF'
#!/usr/bin/env bash
echo "=============================================================="
echo " RECORDING HYGIENE: log into amazon.in BEFORE starting this"
echo " recording. NEVER type passwords, OTPs, or API keys while the"
echo " recorder runs — everything on screen ends up in the video."
echo "=============================================================="
read -rp "Logged in already, nothing sensitive on screen? [y/N] " OKGO
case "$OKGO" in [yY]*) ;; *) echo "Aborted — log in first."; exit 1 ;; esac
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
cat > "$HOME/.local/bin/dtlab-cart" <<'EOF'
#!/usr/bin/env bash
# Run by the PARTNER after each agent run: cart screenshot + parsed cart
# contents (cross-checked against the agent's picks at pack time).
exec python3 "$HOME/dtlab/tools/capture_cart.py" "$@"
EOF
cat > "$HOME/.local/bin/dtlab-verdict" <<'EOF'
#!/usr/bin/env bash
# Guided verdict/rating/rationale capture after each day's runs.
exec python3 "$HOME/dtlab/tools/capture_verdicts.py" "$@"
EOF
chmod +x "$HOME/.local/bin/"dtlab-*
grep -q 'dtlab PATH' "$HOME/.bashrc" || cat >> "$HOME/.bashrc" <<'EOF'
# dtlab PATH
export PATH="$HOME/.local/bin:$PATH"
export DISPLAY="${DISPLAY:-:1}"
alias chromium-browser=chromium
EOF

echo "== [7/7] Done =="
echo ""
echo "Setup complete. Open the 'Lab Desktop' forwarded port (6080) in your"
echo "browser — password printed above (or 'dtlab' if rotation failed)."
echo "KEEP THE PORT PRIVATE. Then use the VS Code terminal for:"
echo "  dtlab-shop | dtlab-start | dtlab-record | dtlab-pack"
