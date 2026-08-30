# Camera Onboarding Runbook

**Status:** First execution complete (`front_of_house`, 2026-08-30)
**Purpose:** Repeatable step-by-step procedure — written so an AI session with no
prior context can follow it — for adding a new camera to Frigate with the same
trigger pattern (object tracking, zones, alert/detection split) built for the
first camera. This *is* HomeLab's Surveillance-Expansion.md Milestone 3, spelled
out at command level from the first real execution.

Do not start this for a second camera until the current one has passed the
Milestone 3 completion gate in
[Surveillance-Expansion.md](projects/Surveillance-Expansion.md) — at least 24
hours of healthy recording with no regression to existing cameras.

## Prerequisites — confirm before starting

- The new camera's location, purpose, retention mode (continuous/motion/live-only)
  and privacy exclusions are already decided and recorded in
  Surveillance-Expansion.md Milestone 1. Do not pick these yourself.
- The camera is physically installed on Cameras VLAN 60, has a DHCP reservation
  in the `192.168.60.100-199` range or a fixed address, and its own unique
  non-administrator credentials (never reuse the `front_of_house` camera's
  credentials).
- The Frigate VM (`192.168.20.10`) is reachable — it must be in
  `.claude/settings.json`'s `sandbox.network.allowedDomains`. If a settings.json
  edit was needed this session, the sandbox network layer needs a session
  restart to pick it up; until then, read-only checks against that host need
  `dangerouslyDisableSandbox: true` on the Bash call (this is expected, not an
  error — CLAUDE.md still requires explicit approval for state-changing SSH
  regardless of sandbox state).
- SSH alias `frigate` already exists and works (`ssh frigate` — no password
  prompt). It maps to `192.168.20.10` as user `jelliott`. Read-only commands over
  this SSH connection do not need to ask first (per CLAUDE.md); state-changing
  commands always do.

## Known structural constraints (do not try to work around these)

- **`jelliott` cannot restart the Frigate service or inspect the Docker
  container.** No passwordless `sudo`, not in the `docker` group. Every
  `frigate-compose.service` restart needs the human to run
  `ssh -t frigate "sudo systemctl restart frigate-compose.service"` themselves
  (the `-t` is required — without it `sudo` fails with "a terminal is required
  to read the password"). Stage everything, then hand off the one command.
- **`jelliott` cannot read `journalctl` output** for this service (not in `adm`
  or `systemd-journal`). Validate a restart using process tree (`ps aux | grep
  frigate`), `systemctl is-active`/`systemctl status` (readable), and fresh
  recording file timestamps instead. For anything journalctl would normally
  catch, point the human at the Frigate UI's own Logs tab.
- **Frigate's web API requires login** (`GET /api/<camera>/latest.jpg` → `401`).
  There is no read-only service account for this today. To see a camera's field
  of view for zone design, ask the human to paste a screenshot from the Frigate
  UI into chat — do not ask for the Frigate password.
- **RTSP credentials live in plaintext inside `config.yaml`** — this is normal
  Frigate design, not a bug. Never echo, log, or paste the RTSP URL (with
  credentials) into chat, a committed file, or this runbook. Redact if you must
  reference it at all.
- **No PyYAML on the Frigate VM or the Mac** as of 2026-08-30. Validate staged
  YAML with `ruby -ryaml -e "YAML.load_file(...)"` (Ruby ships with macOS) as a
  fallback if `python3 -c "import yaml"` isn't available.

## Steps

### 1. Firewall

Add a narrowly scoped OPNsense rule: Frigate (`192.168.20.10`) → new camera IP,
permitting only the ports the camera actually needs (HTTP management, RTSP 554,
ONVIF — check the camera's own docs; do not open more than
`front_of_house`'s baseline of TCP 80/554/8000 unless the model requires it).
**This is a firewall/security-structure change — always confirm with the human
before applying, per CLAUDE.md, regardless of what else is pre-approved.**

### 2. Add the camera to `config.yaml`

SSH in read-only first and pull the current config to see the live structure
(it will have drifted from what's documented — check, don't assume):

```
ssh frigate "cat /opt/frigate/config/config.yaml"
```

Add a new block under `cameras:` (and under `go2rtc.streams:`) following the
`front_of_house` pattern: two go2rtc streams (main/sub), an `ffmpeg.inputs`
block with `record`+`audio` role on the restreamed main and `detect` role on
the sub, `detect.width/height` matching the substream's actual aspect ratio
(not copy-pasted from `front_of_house` — check the new camera's real substream
resolution first).

### 3. Design zones and the object list

- Ask the human to confirm the object classes worth tracking for this camera
  (start from `[person, car]` as the established baseline; only add more if the
  human asks).
- Get the field of view (screenshot from the human, per the constraint above).
  Describe proposed zones in terms of visible landmarks (not raw coordinates)
  and get explicit confirmation before writing anything.
- Convert confirmed zone boundaries to percentages of frame width/height, then
  to absolute pixel coordinates matching this camera's own `detect.width` /
  `detect.height` (not `front_of_house`'s 1920×576 — every camera's detect
  resolution can differ).
- Add a `zones:` block under the new camera and a `review.alerts` /
  `review.detections` split scoped to the new zones, following the pattern in
  `front_of_house`'s config (`docs/07-Surveillance.md` has the authoritative
  current state).
- Leave `face_recognition` and `lpr` disabled unless the human has explicitly
  approved enabling them for this camera — per Surveillance-Expansion.md, that
  is its own scoped decision, not a default.

### 4. Stage, back up, validate — do not restart yet

```
ssh frigate "cp /opt/frigate/config/config.yaml /opt/frigate/config/config.yaml.before-<short-change-name>-$(date +%Y%m%d-%H%M%S)"
```

Write the full new config to `config.yaml.new` (never overwrite `config.yaml`
directly — always stage, diff, then hand off the swap). Confirm the diff shows
*only* the intended additions:

```
ssh frigate "diff -u /opt/frigate/config/config.yaml /opt/frigate/config/config.yaml.new"
```

Validate YAML syntax (see PyYAML/Ruby fallback above) before asking the human
to apply anything.

### 5. Hand off the apply step

Give the human exactly two commands, in order:

```
ssh frigate "mv /opt/frigate/config/config.yaml.new /opt/frigate/config/config.yaml"
ssh -t frigate "sudo systemctl restart frigate-compose.service"
```

### 6. Validate after restart

```
ssh frigate "systemctl is-active frigate-compose.service; ps aux | grep frigate | grep -v grep; find /opt/frigate/storage/recordings -type f -name '*.mp4' -newermt '-2 min' | head"
```

Look for: `active`, a full Frigate process tree (`frigate.detector`,
`frigate.capture:<camera>`, `frigate.process:<camera>`, plus ffmpeg pipelines
for the new camera), and fresh recording segments for **both** the existing and
new camera — confirm no regression to `front_of_house`.

### 7. Observe, then document

- Per Milestone 3: observe at least 24 hours of healthy recording (both
  cameras) before onboarding another.
- Update `docs/07-Surveillance.md` (baseline), `docs/VLAN-Design.md` (device
  table), `configs/devices.conf` and `configs/services.conf` (add the new
  camera's SSH-alias-equivalent row if it gets one), and check off the relevant
  Milestone 3 items in `Surveillance-Expansion.md`, including an Evidence Log
  entry.
- Commit documentation updates directly to `main` (established project
  convention — see auto-memory `feedback-direct-main-pushes`); config changes
  on the VM itself are never committed to Git (credentials).

## Change log

| Date | Camera | Change | Notes |
|---|---|---|---|
| 2026-08-30 | `front_of_house` | Added `objects.track: [person, car]`, zones (`driveway`, `porch`, `street`), `review.alerts`/`detections` split, disabled `face_recognition`/`lpr` | First execution of this runbook (retroactively, since the runbook was written from this session). Backup: `config.yaml.before-triggers-20260830-103233`. Restarted 10:35:19 PDT, confirmed healthy: stable process tree, recordings flowing, no regression. |
