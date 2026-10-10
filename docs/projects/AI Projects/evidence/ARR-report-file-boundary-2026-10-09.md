# Offline ARR report file-boundary review — 2026-10-09

**Status:** local candidate only; no deployed code changed.

`get_arr_report` already permits only six named services and bounded aggregate
health, queue and import counters. It checks freshness and rejects unknown
fields. That makes “Is SABnzbd up?” a deterministic Aster report question;
routine status does not need Codex reasoning or a new connected tool.

The file reader previously checked `lstat()` and then reopened the pathname.
The candidate validates the opened inode and reads at most 65,537 bytes, so a
pathname replacement cannot bypass the size/type check. It opens without
following a final-component symlink and without blocking on a FIFO. Existing
schema, coverage, counter and repair-candidate rules are unchanged. Fifteen
focused ARR tests pass, including symlink, FIFO, writable and oversized input.

A read-only metadata check found the live LXC 104 report to be a regular
`root:aster` file, mode `0640`, 940 bytes at the recorded check time. No report
contents, credentials or queue details were read. This is file-boundary
hardening, not proof that the report was fresh, correct or that a particular
service was healthy. Before deployment, compare the exact deployed source and
producer versions, run the full application fixtures in its normal environment,
and retain the prior reader for rollback.

This change must not be interpreted as permission to pass the report or any
repair candidate to Codex. A future read-only Codex investigation needs a
separate fixed-target projection, M1 identity/authority gate, privacy review,
and measured utility beyond a deterministic status answer.
