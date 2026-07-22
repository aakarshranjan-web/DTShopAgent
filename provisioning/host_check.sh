#!/usr/bin/env bash
# host_check.sh — run on the student's OWN machine (macOS / Linux) at T-14.
# Answers: can this laptop run the lab VM, and which image should I download?
# No admin rights needed; read-only checks; prints a verdict.
set -uo pipefail
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; N='\033[0m'
PASS=1
ok(){ echo -e "${G}[ok]${N} $1"; }
warn(){ echo -e "${Y}[??]${N} $1"; }
fail(){ echo -e "${R}[!!]${N} $1"; PASS=0; }

echo "== Digital Twin Lab — host compatibility check =="
OS="$(uname -s)"; ARCH="$(uname -m)"
echo "System: $OS / $ARCH"

# --- architecture -> which image ---
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
  IMAGE="dtlab-arm64.utm  (hypervisor: UTM, free from getutm.app)"
elif [ "$ARCH" = "x86_64" ]; then
  IMAGE="dtlab-amd64.ova  (hypervisor: VirtualBox)"
else
  fail "Unsupported architecture $ARCH — use the Codespaces fallback route."
  IMAGE="(none — Codespaces fallback)"
fi

# --- virtualization capability ---
if [ "$OS" = "Darwin" ]; then
  if [ "$(sysctl -n kern.hv_support 2>/dev/null)" = "1" ]; then
    ok "Hardware virtualization supported (Hypervisor.framework)"
  else
    fail "No hypervisor support detected — Codespaces fallback."
  fi
else
  if grep -qE 'vmx|svm' /proc/cpuinfo 2>/dev/null; then
    ok "CPU virtualization flags present (VT-x/AMD-V)"
  else
    fail "VT-x/AMD-V not visible. Often DISABLED IN BIOS/UEFI — enable
     'Intel VT-x' / 'AMD-V' / 'SVM Mode' in firmware settings, then re-run.
     If it still fails (common on locked corporate laptops): Codespaces."
  fi
fi

# --- RAM: host needs headroom above the guest allocation ---
if [ "$OS" = "Darwin" ]; then
  RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
else
  RAM_GB=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1048576 ))
fi
if [ "$RAM_GB" -ge 16 ]; then ok "RAM: ${RAM_GB} GB — give the VM 8 GB"
elif [ "$RAM_GB" -ge 12 ]; then ok "RAM: ${RAM_GB} GB — give the VM 6 GB"
elif [ "$RAM_GB" -ge 8 ]; then warn "RAM: ${RAM_GB} GB — set the VM to 5 GB
     and close everything else during the lab. Workable, not comfortable."
else fail "RAM: ${RAM_GB} GB — too little to host the VM. Codespaces."
fi

# --- disk ---
FREE_GB=$(df -Pk "$HOME" | awk 'NR==2 {print int($4/1048576)}')
if [ "$FREE_GB" -ge 30 ]; then ok "Free disk: ${FREE_GB} GB"
else fail "Free disk: ${FREE_GB} GB — need ~30 GB (image + VM growth)."
fi

echo ""
if [ "$PASS" = "1" ]; then
  echo -e "${G}VERDICT: this machine can run the lab VM.${N}"
  echo "Download: $IMAGE"
  echo "Next: import it, boot, and complete the T-7 smoke-test checkpoint."
else
  echo -e "${R}VERDICT: use the Codespaces fallback route${N} (see handout) —"
  echo "or fix the [!!] items above and re-run this check."
fi
