# F2 first-failure correction — independent Stream A review — 2026-10-20

Status: **SOURCE REVIEW PASS; UNINSTALLED; NO NEW SCAN AUTHORIZED**

Stream A reviewed platform commit
`183e7cfcc6d5de9c6e1da0d7f86c0cc8269f80c9` after the October 20
exact-cycle NO-GO exposed loss of the preparation failure phase.

## Verified properties

- a preparation `no_go` is terminal and survives a later final invocation;
- `first_failure_phase` is restricted to `prepare` or `final`;
- `failure_class` comes from a fixed content-free allowlist;
- raw exception messages, commands and paths are not persisted in the state;
- the final attempt does not retry preparation or invoke the observer after a
  terminal preparation failure;
- timeout behavior still kills the observer process group and records the
  bounded `OBSERVER_TIMEOUT` class.

The two frozen source hashes independently match the platform card:

| Path | SHA-256 |
|---|---|
| `scripts/local-ai/f2_scheduled_release_candidate.py` | `aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23` |
| `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `df4d3402bff12f362432d53fc57af072eb67897a848864cc8da3eb706f5b2bf0` |

Stream A extracted the committed source into an isolated temporary directory
and reran the focused suite: **10/10 passed**. The platform owner separately
reports **344 passed, 8 expected skips** for the full local suite and **10/10**
on target Linux. This independent review confirms the correction's intended
source boundary; it does not independently reproduce the full target-Linux
suite.

## Remaining gate

The correction is not installed. A reviewed inactive installation with exact
rollback and installed-path proof must precede any fresh schedule. Even after
installation, a new cycle needs a fresh card and explicit approval. The failed
October 20 cycle remains closed, and F3/F4/full-stop/A1 remain blocked.

