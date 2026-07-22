# VM distribution — which hypervisor, and the pre-built rollout

## The short answer

There is no single free hypervisor that covers a modern MBA cohort with one
image, because the cohort's laptops span two CPU architectures. Plan for two
builds of the same golden image:

| Student hardware | Hypervisor (free) | Image you distribute |
|---|---|---|
| Windows, Linux, Intel Macs | **VirtualBox** (free, GPL; the primary path) | `dtlab-amd64.ova` — double-click import |
| Apple Silicon Macs (M1–M4; expect a third of the room) | **UTM** (free from getutm.app; the App Store copy is the paid convenience version) | `dtlab-arm64.utm` bundle — built from Ubuntu 24.04 **arm64** with the same `provision.sh` |
| Fallback for either | VMware Workstation Pro / Fusion (free for personal use since 2024) | imports the same `.ova` (amd64) |

Do **not** try to run the amd64 `.ova` under emulation on Apple Silicon —
QEMU x86 emulation is 10–20x too slow for an agent driving a browser. The
arm64 build is native-speed and everything in the kit (Hermes, Playwright,
Chromium, the Python tools) ships arm64 Linux builds.

If wrangling two images is unattractive, the clean alternative is one
**cloud VM per student** (a small 2-vCPU/8GB instance with a desktop +
browser accessed via web VNC) — identical for everyone, nothing installed
locally, ~$1–3 per student for the lab week on any major cloud's education
credits. More instructor setup, zero student-side hypervisor support. The
local-VM path remains the default in this kit; the cloud path is the escape
hatch if the pilot reveals too much hypervisor friction.

## Building the two images (instructor, once)

1. Create a clean Ubuntu 24.04 **Desktop** VM in VirtualBox (amd64) and in
   UTM on any Apple Silicon machine (arm64, "Virtualize" mode, not
   "Emulate"). 4 vCPU / 8 GB / 40 GB each.
2. Create user `student` with the course password; enable auto-login.
3. Copy the `dt-lab` kit into the VM and run `provisioning/provision.sh`.
4. Run `hermes setup` interactively: provider = Anthropic, API key left
   blank, browser automation = local mode. Do one `/browser connect` smoke
   test so first-run downloads are cached in the image.
5. Clear shell history, delete any test keys, `sudo apt clean`.
6. Export: VirtualBox → File > Export Appliance → `dtlab-amd64.ova`
   (~6–9 GB). UTM → right-click VM > Share → `dtlab-arm64.utm.zip`.
7. Distribute via the LMS or a OneDrive/Drive link, with per-platform
   one-page import instructions (import → boot → `dtlab-start`).

## Student rollout experience (what "pre-built" means here)

Install VirtualBox or UTM (one download, no admin knowledge), import the
image (one double-click / drag), boot. Everything else — Hermes, browser,
Playwright, scripts, templates, aliases — is already inside. The only
things a student ever types are:

    dtlab-shop       # FIRST: the student's own logged shopping + pick confirmation
    dtlab-start      # then the agent run (pre-flight enforces the ordering)
    dtlab-record     # screen capture during the agent run
    dtlab-pack       # builds the single submission zip at the end

The manual-install route (`provision.sh` on their own machine) remains
documented for the handful of students who want it, but it is optional and
unsupported in office hours — the image is the paved road.

## Route decision (updated)

With GitHub Classroom off the table and datacenter-IP CAPTCHA friction
confirmed as a real cost, **local VMs are the primary route** and the
Codespaces config (`.devcontainer/` at the repo root) was temporarily demoted to a fallback for students whose
laptops cannot run a VM. Note that the human-first protocol (dtlab-shop
before the agent) is itself the main CAPTCHA mitigation on ANY route: the
agent inherits a session warmed by genuine human shopping, on the student's
account, minutes earlier — on a local VM that session also carries a
residential IP, which is why local-first wins.

## "How do we KNOW the local VMs will work?" — the testing funnel

Local machines fail in predictable ways; the answer is not hope but a
staged funnel with a fallback at every stage, so every failure surfaces
early and lands somewhere soft:

| Stage | When | What | Failure lands in |
|---|---|---|---|
| 0. Instructor dry run | T-21 | Full lab (host check → import → dtlab-shop → agent run → dtlab-pack) on THREE machines: a Windows laptop with Hyper-V active, an Apple Silicon Mac, an 8 GB budget laptop. These three cover ~90% of real failure modes. | fix the kit |
| 1. Host check | T-14 | Student runs `host_check.sh` / `host_check.ps1` on their own machine (read-only, no admin). Verdict: which image, what VM RAM to set, or "Codespaces fallback". Screenshot to LMS. | Codespaces route |
| 2. Import + boot | T-10 | Import image, boot, log in. | office-hours triage (below) |
| 3. Graded smoke test | T-7 | `dtlab-start` pre-flight passes on placeholder data + agent completes the books.toscrape.com sandbox task. Screenshot to LMS. | Codespaces route, no grade penalty |
| 4. Data readiness | T-3 | Persona + history ingested; twin quiz passes. | office hours |

The rule that makes this robust: **nobody debugs a hypervisor on lab day.**
Anyone not green at stage 3 by T-5 is moved to Codespaces automatically —
that's exactly what the fallback route is for, and the datacenter-IP
CAPTCHA cost is acceptable for the residual few.

## Triage table (tape this to the office-hours desk)

| Symptom | Cause | Fix |
|---|---|---|
| VirtualBox: "VT-x is not available" / VERR_VMX_NO_VMX | Virtualization off in BIOS | Enable VT-x / SVM in firmware; if firmware is locked (corporate device) → Codespaces |
| VM extremely slow on Windows, green-turtle icon in VirtualBox status bar | Hyper-V owns the hypervisor (WSL2/Docker Desktop) | Acceptable if usable; else disable "Virtual Machine Platform" + "Windows Hypervisor Platform" and reboot, or → Codespaces |
| Import fails / image "corrupt" | Truncated download | Re-download; verify the SHA-256 the instructor publishes next to the image |
| Host freezes during run | RAM overcommit | Lower VM RAM per host_check verdict; close browser on host |
| UTM VM won't boot on Mac | Student grabbed the amd64 image or chose "Emulate" | arm64 image, "Virtualize" mode |
| Black screen in VM after boot | 3D acceleration glitch | Disable 3D acceleration in VM display settings |
| No internet in VM | VPN or captive portal on host | Disconnect VPN / use NAT networking (default) |

Publish the image SHA-256 hashes alongside the download links; `host_check`
plus a hash check removes the two most common "mystery" failures
(incapable host, corrupt download) before they ever reach office hours.
