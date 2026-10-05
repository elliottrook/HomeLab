# Integrated fixture probe candidate — 2026-09-26

Status: complete local candidate submitted for final technical review; all live
entry points/default spawn/socket factories remain disabled. No LXC100 invocation.

The preceding collector checkpoint was independently reviewed and committed at
`50500ff`. Its candidate manifest is historical at that commit. The manifest for
this revision is `lxc100-integrated-manifest.json`; it pins collector/guard sources,
argv catalog, parsers, lifecycle, journal, payload, plan and local tests. The exact
runtime cleanup argv additionally hashes its strictly typed ownership receipt.
Pins establish reviewed content identity, not signatures or tamper-proof authority.

## Flow and durable evidence

The integrated controller uses the previously reviewed preflight, health, DNS,
resource/property and denial-check semantics directly. It does not translate real
ownership into the fake state's invented invocation string. FixedSession remains
the only subprocess seam; tests replace it with invented local child programs.

Sequence: absent unit/paths → healthy baseline and two DNS queries → durable create
intent → exclusive canary creation plus identity readback in one remote proposal →
durable run intent → readiness and observed PID/invocation/cgroup/property binding →
verified exit and exact two-line output → health/DNS comparison → durable cleanup
intent → guarded cleanup → absence check → final health/DNS comparison → complete.

`systemd-run --quiet` suppresses normal status banners; any remaining stderr fails
closed. This is a command revision requiring review, not silently accepted output.
The guard receives only bounded integer stat fields, PID, hexadecimal invocation
ID and the Boolean completion flag; no user-controlled command or path parameter.

A newly created 0700 local journal holds exclusive 0600 sequence files, SHA256
previous-record links, fsync before proceeding and a process lock. Intent precedes
every mutation. It stores sanitized observations/response hashes, DNS timing and
ownership receipts; no credentials or accepted pilot content. Each record is at
most 8 KiB, at most 64 records. Partial/corrupt/gapped/symlink records are rejected,
never overwritten. Hash chaining detects accidental corruption; a malicious local
owner/root could rewrite the entire chain. Power-loss persistence is not empirically
proven by these process-interruption tests and filesystem fsync calls.

## Recovery and already-unloaded unit

An existing journal is never accepted as a new run. Recovery returns durable
ownership/last event and forbids automatic stop, deletion and rerun. Corruption
requires human inspection. A lost response, missing ownership, unexpected state or
interrupted cleanup remains manual recovery, even if a path happens to look right.
No generic stop/reset/remove command is issued by the integrated lifecycle.

During an uninterrupted, successfully completed run only, guarded cleanup accepts
an inactive original invocation OR an already-unloaded/not-found unit with empty
invocation and PID zero. Both require absent cgroup, absent unexpected runtime
probe, and the exact recorded directory/file device+inode, root ownership, modes,
link count and one-byte content. The guard opens the directory without following
symlinks, unlinks relative to its descriptor and rechecks identity before rmdir.
A mismatched/replaced/running unit or canary rejects deletion. Failures retain the
receipt for manual diagnosis; they never stop/delete by name alone.

## Validation

184 full tests pass, including 8 new integrated/journal/guard tests (with subcases).
Coverage includes each fixed operation failing, six durable interruption points,
exclusive journal access, corruption/gap/symlink rejection, no automatic replay,
loaded and already-unloaded guards, invocation/inode/running/cgroup mismatches,
child reaping, and default denial. All guard system calls in guard tests are mocks;
all process integration children are local invented fixtures. No real DNS query,
SSH, unit start, canary write/removal on LXC100, or accepted-corpus evaluation.

## Precise remaining risks and final-review decisions

- This is an implementation candidate, not proof of LXC confinement. Actual nested
  LXC/systemd properties, seccomp support, output formats, CPU/memory limits and
  household-service behavior remain UNKNOWN until the narrowly approved probe.
- The implementation deliberately does not automatically stop a unit on uncertain
  identity/transport failure. It relies on the proposed 15-second unit lifetime,
  then manual recovery if state cannot be verified. That lifetime is unproven on
  LXC100; this differs from the older name-based stop fallback and needs explicit
  technical acceptance before a live run. Local SSH termination cannot prove
  remote process termination.
- Five seconds of worker inspection may be too short for multiple SSH queries.
  A missed window is inconclusive and requires manual recovery; no automatic retry
  or enlargement is authorized. Health queries are bounded but add shared-host load.
- A concurrent privileged administrator can replace same-name units or filesystem
  objects between comparisons and system calls. No portable atomic systemd
  compare-and-act exists in this candidate. The guard narrows races but cannot
  defeat malicious/concurrent root. Require an exclusive operator maintenance
  window for this fixed probe; otherwise do not run it.
- Creation or cleanup interrupted after a partial filesystem mutation can leave
  the one-byte canary or empty directory. Never delete an unfamiliar replacement.
  Human recovery must compare the receipt with fresh read-only observations.
- Existing generic proposal commands remain historical design objects. This
  controller never invokes their name-only stop/reset/remove operations. Trusted
  test injection is not a sandbox against malicious Python callers.
- The manifest is a review artifact; current runtime verifies the caller-provided
  catalog pin, not every source file against an independently trusted signature.
  Before enabling a live adapter, verify every manifest artifact and preserve the
  reviewed manifest externally. Keep live entry disabled on any mismatch.
- Accepted-corpus/model evaluation, installation, additional infrastructure changes
  and Git push remain excluded. A successful fixture probe would prove only this
  bounded feasibility check, not authorize the accepted-corpus experiment.
