# MacBook bootstrap manifest

> Part of [MacBook Administration Layer](../projects/MacBook-Administration-Layer.md), M1.
> Records what the local HomeLab admin toolkit (`lab`, `scripts/doctor.sh`, `scripts/backup/*.sh`)
> actually needs to run on the MacBook, and what was verified present — not an assumed or
> invented version pin. Re-verify and update this file if the toolkit's dependencies change.

## Scope

This manifest covers only the local admin-toolkit surface used from a normal interactive
shell on the MacBook: `lab` and the scripts it calls (`doctor.sh`, `scripts/backup/*.sh`,
`scripts/api-get.sh`, `scripts/lib/output.sh`). It does not cover building or running other
parts of this repository (e.g. the AsterCompanion Swift app, Python services meant to run on
lab LXCs) — those have their own tooling and are out of M1's scope.

## Host verified

- macOS 26.5.2 (build 25F84), Darwin 25.5.0, arm64 (Apple Silicon) — confirmed both via a
  temporary M0 SSH inventory pass and again directly on-machine during M1; no drift.
- FileVault: On.
- Xcode Command Line Tools already installed at `/Library/Developer/CommandLineTools`.

## Dependency scan

`scripts/lab`, `scripts/doctor.sh`, `scripts/backup/*.sh`, `scripts/api-get.sh` and
`scripts/lib/output.sh` were scanned for external command usage (excluding remote commands
executed over `ssh`/`pct exec` on lab hosts themselves, which run on those hosts, not the
MacBook). Real local dependencies: `bash`, `ssh`, `scp`, `nc`, `curl`, `git`, `python3`,
`rsync`, `sqlite3`, `shasum`. (Two earlier grep passes for `age` and `node` were false
positives — substring matches on variable names like `backup age` and `node_json`; neither
binary is actually invoked by this toolkit.)

Every one of those is already present on this MacBook via the Apple-provided base system
and Xcode Command Line Tools — **no Homebrew install was needed or performed** for the core
toolkit to run. Versions actually observed, 2026-09-24:

| Tool | Path | Version observed | Notes |
|---|---|---|---|
| bash | `/bin/bash` | 3.2.57(1) | Apple's stock (GPLv2-frozen) bash; no bash 4+ syntax needed by these scripts |
| zsh | `/bin/zsh` | (default login shell, dscl-confirmed) | — |
| git | `/usr/bin/git` | 2.50.1 (Apple Git-155) | matches mini per M0 inventory |
| ssh / scp | `/usr/bin/ssh` | OpenSSH_10.2p1, LibreSSL 3.3.6 | — |
| curl | `/usr/bin/curl` | 8.7.1 | universal binary; `curl --version` reports an x86_64 slice string even though the host is arm64 — cosmetic only, confirmed no Rosetta translation is occurring (`sysctl sysctl.proc_translated` = 0) |
| python3 | `/usr/bin/python3` | 3.9.6 (Apple stub) | every inline `python3 -c` use in `doctor.sh` imports only `json`/`sys` from the standard library — no third-party packages required |
| nc | `/usr/bin/nc` | (BSD nc) | used by `lab health` / `lab status` port checks |
| rsync | `/usr/bin/rsync` | openrsync, protocol 29 | Apple replaced classic rsync with `openrsync`; the two flag sets this toolkit actually uses (`-rlt`, `-rltc` in `scripts/backup/synology-proxmox-pull.sh`) are supported. Worth re-checking if a future change adds a classic-rsync-only flag (e.g. `--info=progress2`). |
| sqlite3 | `/usr/bin/sqlite3` | 3.51.0 | — |
| shasum | `/usr/bin/shasum` | 6.02 | — |
| jq | `/usr/bin/jq` | jq-1.7.1-apple | present via Apple's own build; not currently called by the core toolkit but available if needed |

Homebrew and Node.js are confirmed **not installed** (per both the M0 remote inventory and a
direct on-machine check during M1) and are **not required** by anything in the core toolkit's
dependency scan above. Nothing was installed to satisfy this milestone. If a future milestone
needs a tool this scan didn't find (e.g. Homebrew for something outside this manifest's scope),
install it only from the tool's own official source (e.g. `https://brew.sh`'s own install
script), never a third-party mirror, and add it to this manifest with the verified version.

## Canonical `lab` command resolution

Confirmed on 2026-09-24:

- No legacy `~/lab/bin/lab` exists on this MacBook (the mini's known-obsolete shadow script,
  per `docs/projects/MacBook-Administration-Layer.md` §2) — nothing to avoid replicating,
  and nothing currently shadows `scripts/lab`.
- No `lab` binary exists anywhere else on a default PATH (`/usr/local/bin`, `/usr/bin`,
  `/bin` all checked).
- Run directly by path, `scripts/lab` (help, `list`, unknown-command, unknown-device cases)
  produces clear, actionable, secret-free output — see the M1 evidence log entry for the
  actual transcript.
- **Not yet resolvable in a normal interactive shell.** No `~/.zshrc`, `~/.zprofile` or
  `~/.zshenv` exists on this Mac yet, so a fresh Terminal PATH is exactly macOS's system
  default (confirmed via `env -i /usr/libexec/path_helper`, independent of anything this
  Claude Code session's own environment injects) — it does **not** include `~/bin`, and
  `lab` does not resolve.
- `~/bin` already exists and already holds one personal script (`arista-console`, a
  `screen`-based wrapper for the same USB-serial device `scripts/lab`'s `arista` command
  uses) — established Jason-created convention for personal executables, reused rather than
  inventing a new location.
- **Planned fix (blocked on explicit confirmation, see evidence log):** symlink
  `~/bin/lab -> ~/lab/homelab/scripts/lab` (so `git pull` updates propagate with no copy to
  keep in sync), and add `export PATH="$HOME/bin:$PATH"` to a new `~/.zprofile`. Writing a
  new dotfile in `$HOME` (outside this repo) was blocked by this session's own
  auto-mode classifier as an "Unauthorized Persistence" action requiring Jason's explicit
  say-so — appropriately, since it's a standing, machine-wide shell-startup change, not a
  repo-scoped edit. Not yet done.

## Bookmarks and offline recovery docs

- "Bookmarks" in this toolkit means `configs/devices.conf`'s `web_url` column, opened via
  macOS's native `open` command by `lab dashboard` / `lab web DEVICE`. These are plain LAN
  URLs (e.g. `http://192.168.1.1` for OPNsense) checked into the repo, not a browser bookmark
  file — reachable as soon as the repo checkout is current and the MacBook has Management/
  Servers VLAN access, both already true (see project doc evidence log, DHCP reservation
  section). No separate action needed.
- Offline recovery documentation (e.g. `docs/05-Backups.md`'s recovery order, the runbooks
  under `docs/runbooks/`) lives in this same `~/lab/homelab` checkout and is reachable now
  that the checkout is current — confirmed by reading it directly during M1. `homelab-wiki`
  and `homelab-reference` (the mini's separate human/second-brain repos) are **not** cloned
  onto the MacBook: neither is required by the core admin toolkit's dependency scan above,
  and cloning them isn't listed as required by this project's own scope (§3) — flagged here
  rather than done, in case Jason wants that reachability guaranteed independently of the
  mini/Aster Wiki LXC in a later milestone.

## Dependency/permission error quality

Spot-checked 2026-09-24 (see M1 evidence log for exact output): `scripts/lab` with no
arguments, an unknown command, and an unknown device name all produce plain, specific,
secret-free messages (e.g. `Unknown device: nonexistent-device` followed by the real device
list). `scripts/doctor.sh`'s `check_backup_age` already handles a missing backup directory
gracefully — `warn "$display backup directory does not exist"` rather than a raw stack trace
or a false PASS — relevant here because `~/lab/private-backups` does not exist on this
MacBook (no backup coverage configured yet, a separate open item tracked for M4). No code
change was needed for either case; both were verified by reading and by direct local
invocation, not assumed.
