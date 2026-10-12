# Home Assistant report freshness recovery — 2026-10-11

**Status:** bounded producer and reader fixes deployed; immediate postchecks and one unattended cron refresh passed. No Home Assistant credential, entity state, control path or Codex tool grant changed.

## Detected drift

The completed Home Assistant advisor project recorded a five-minute, root-owned Proxmox producer and a fresh report on 2026-09-10. A read-only check on 2026-10-11 found LXC 104's schema-1 saved report still dated `2026-09-10T11:29:38.150524Z`; the installed Aster reader correctly returned `unavailable`. This is verified current degradation of the report-backed *live-status* feature, not evidence that Home Assistant itself was down or that its other knowledge answers failed.

The Proxmox cron file `/etc/cron.d/aster-ha-report` still scheduled `/usr/local/sbin/refresh-and-push-aster-ha-report` every five minutes, and cron logs showed recent invocations. The installed producer and wrapper hashes matched the tracked scripts. The producer called bare `qm` while Proxmox provides it at `/usr/sbin/qm`. A manual run with the interactive root path succeeded and wrote a private candidate. The same producer under `PATH=/usr/bin:/bin` failed with `FileNotFoundError` before writing a candidate. This reproduced the scheduling-environment cause without printing the guest agent's raw Home Assistant response.

## Bounded change and recovery

The producer now invokes `/usr/sbin/qm`. A regression test asserts the absolute command path; both producer tests pass. Under cron's restricted path, the staged candidate exited zero and produced an exact top-level schema-1 report of 475 bytes. The first Python compilation attempt tried to write outside the workspace and was rejected by the sandbox; compilation succeeded with a private temporary bytecode cache. No dependency was installed.

Before replacing the live producer, its SHA-256 was `218bcb51a9765f34449395f2898330b2c26b14d0a2dd458bc20f88bb501d8704`; the candidate was `d1af2e7e53c0750f16f7edd3a28ed7360e65000a26e7846bd0a487523b0429a3`. Exact hash checks guarded an atomic replacement. The original root-owned executable remains at `/usr/local/libexec/rollback-produce-aster-ha-report-before-cron-path-20261011.py`. Restoring that file is possible but would restore the known cron-path defect; for a new failure, stop the cron job and investigate before choosing rollback. The wrapper, cron schedule, VM 103 and its guest configuration were unchanged.

One source-local wrapper run under the restricted path exited zero and delivered a fresh report to LXC 104 at `2026-10-12T04:33:22.741360Z`. As `aster`, the existing reader accepted it. The wrapper's transient report may contain approved aggregate fields, but no report body, guest-agent output, credential or private entity state was copied into this evidence record.

The Home Assistant reader itself had three narrow fail-closed defects: a path-bearing OS error, a two-open file race, and unhashable JSON status values raising `TypeError`. Its local candidate uses one no-follow descriptor, bounded read and fixed file-error messages, and type-checks status before set membership. The existing installed source differed only by those candidate edits. The HA/ARR/gateway focused suite passed 115 tests. A staged copy read the new live report and rejected a synthetic malformed status. Exact hash checks guarded a separate atomic replacement and one `aster-agent.service` restart. The old reader hash `c82e8a9cb717eb043eaddb2a3c95c7b263a58a3fb64fc0a3b562e0922d8f1ce2` is retained at `/opt/aster-agent/rollback-ha-report-before-parser-20261011.py`; installed SHA-256 is `9d99e511a123fb5a73c93aceb17af7ea7ebbeb442e437798b2c5cfadbdeece81`.

After that restart, Aster was active/running with zero recorded restarts, `/health` returned OK, the service account could read the fresh HA report, and a missing report returned `unavailable` without its private basename. The next unattended five-minute cron run advanced the report timestamp to `2026-10-12T04:35:06.112779Z`; a read-only source-local check found it 14 seconds old. These checks verify one scheduled refresh and parser behavior, not the semantic correctness of every Home Assistant field, long-term delivery reliability or model answer quality.

## Local monitoring candidate

`scripts/doctor.sh` now has a separate check for the HA report file's update age, with a 15-minute limit and explicit missing/future-timestamp results. This would have flagged the month-old file on the next Doctor run. It reads only file metadata; a recently touched but malformed report can still pass this *file freshness* check, while the Aster reader separately validates content and age. The candidate is committed locally only; it is not represented as a deployed alert or an always-on monitor. `bash -n` and the six existing Doctor video-archiver tests passed; a read-only `stat` against the current LXC 104 path returned a numeric epoch.

The same local Doctor edit removes the old Vulkan-specific inference assertion. The current check can truthfully establish the Aster API response, active llama.cpp service, `xe` driver binding and VM-105 isolation, but not actual SYCL GPU offload. It now says so explicitly. Full active-backend/offload health remains with B60 inference engineering and needs its own evidence before Doctor claims it.
