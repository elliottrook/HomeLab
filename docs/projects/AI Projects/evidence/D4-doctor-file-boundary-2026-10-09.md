# Offline Doctor report file-boundary review — 2026-10-09

**Status:** local candidate only; not deployed or enabled.

The first read-only investigation path consumes one fixed Doctor report. Review
found that the adapter previously called `stat()` and then `read_bytes()` on
the pathname. A replacement between those calls could evade the size check;
following a symlink also contradicted the intended fixed-file boundary.

The candidate opens the report once without following a final-component
symlink, rejects non-regular or group/other-writable files, checks the opened
file's size, and reads at most 65,537 bytes before parsing. The observation
still contains only aggregate status, check count, and report digest. Doctor
summaries and raw report bytes do not enter the incident record. Missing or
unsafe input yields `unavailable`; there is no refresh or retry.

Focused adapter and investigation tests pass (nine tests), including symlink
and writable-file rejection. The gateway fixture suite could not run in the
system Python because FastAPI is absent; no dependency was installed for this
offline check. A read-only check on LXC 104 found the live report to be a
regular `root:aster` file, mode `0640`, 3,403 bytes, under a `root:aster`
directory, mode `0750`. No report contents or secret-bearing file were read.
The live adapter hash (`9aa2fd804ff3b8ee…`) differs from the local candidate
(`1a167a3ae492eaba…`), confirming this change is not deployed. Recheck the
mode and source hash at any future deployment gate. This candidate does not satisfy the separate
Stage2 identity gate, prove diagnostic usefulness, or authorize connected
Codex tools. Deployment needs its own gate, source-hash comparison, normal
authenticated fixture check, and rollback to the prior adapter.
