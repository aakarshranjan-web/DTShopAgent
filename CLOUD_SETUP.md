# Cloud route — identical free environments via GitHub Codespaces

> **STATUS: fallback route.** The course runs GitHub-Classroom-free and the
> datacenter-IP CAPTCHA cost is real, so local VMs (VM_DISTRIBUTION.md) are
> primary. Keep this route for students whose laptops can't run a VM; the
> human-first protocol (dtlab-shop before the agent) partially offsets the
> IP problem even here, because the agent takes over a human-warmed session.

## Can this be done on a free cloud VM? Yes — with one honest caveat.

**Recommended free path: GitHub Codespaces + GitHub Classroom.** Every
student gets the *bit-identical* container environment defined in
`.devcontainer/` (at the repo root) — same OS, same Hermes version, same browser, same tools —
launched from a browser link with zero local installation, on Windows,
Intel Mac, Apple Silicon, or a library computer alike. This dissolves the
two-architecture VM problem entirely.

Why it's free:
- Verified students get free Codespaces use, up to 180 core-hours per month
  on their personal accounts (GitHub Student Developer Pack; MBA students
  qualify via university email). On the 2-core / 8 GB machine this config
  requests, that's ~90 machine-hours/month — the whole lab needs maybe 10.
- Alternatively, run it through **GitHub Classroom**: codespaces launched
  in assignment repos bill to the classroom organization's education
  allowance, not to students — so students don't even need the Student
  Pack, just a GitHub account. Verify current quotas against GitHub's
  education docs at term start; allowances have shifted over the years.

How it works for the student:
1. Accept the GitHub Classroom assignment link → "Create codespace".
2. Wait ~4 min for first build (the setup script installs everything).
3. Click the auto-forwarded **Lab Desktop** port → a Linux desktop opens
   in a browser tab (noVNC, password `dtlab`). Chromium runs there.
4. Use the VS Code terminal for the same three commands as the VM route:
   `dtlab-start`, `dtlab-record`, `dtlab-pack`.
5. The packed evidence zip is downloaded via the VS Code file explorer
   (right-click → Download) and uploaded to the LMS.
6. **Stop the codespace when done** (it also auto-suspends after 30 min
   idle) — core-hours only burn while running.

Instructor setup (once): create the course GitHub organization, apply for
GitHub Education teacher benefits, make a template repo containing this
kit (`.devcontainer/` is at the repo root already). Do one full dry run yourself — including a real amazon.in
session — before committing the cohort to this route.

## The one honest caveat: datacenter IPs

Codespaces egress from Microsoft Azure datacenter IP ranges. Amazon's
anti-bot systems treat datacenter traffic with more suspicion than the
residential IPs a local VM inherits from the student's home connection.
Expect: more frequent login verification (OTP emails/SMS), more CAPTCHAs
mid-session, and a small but real chance of an account being temporarily
flagged. The design already mitigates the worst of it — the student logs
in manually, the agent's SOUL stops at every CAPTCHA for human handling,
and actions run at human pace — but the friction is genuinely higher than
on a local VM.

**Decision rule:** dry-run the full lab from a codespace yourself. If your
amazon.in session behaves (one OTP at login, occasional CAPTCHA), adopt
Codespaces as the primary route and keep local VMs as the fallback for any
student whose account gets cranky. If Amazon fights you throughout the dry
run, invert it: local VMs primary (VM_DISTRIBUTION.md), Codespaces as the
fallback for students whose laptops can't run a VM.

## Rejected free alternatives (so you don't re-litigate them)

- **Oracle Cloud "Always Free"** (4 Arm cores / 24 GB — the most generous
  true free tier): requires each student to open their own cloud account
  with a credit card, signups are frequently rejected, and free-tier
  capacity is often unavailable in popular regions. Not classroom-reliable.
- **AWS/GCP/Azure free tiers**: the always-free instance sizes (~1 GB RAM)
  cannot run a desktop + Chromium + agent.
- **Google Cloud Shell**: free but ephemeral and storage-limited; sessions
  reset. No.
- **Instructor-provisioned cloud fleet on education credits** (one script
  spins up N identical VMs with web desktops; students get a URL): the most
  controlled option and effectively free via university cloud-credit
  programs, but it makes the instructor the fleet's sysadmin for the week
  and shares the same datacenter-IP caveat. Keep as plan C.
