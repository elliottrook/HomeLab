# LXC100 feasibility supervisor — local fixture evidence

Status: candidate awaiting technical review before commit or user run request.
No remote mutation, accepted corpus access, unit start or live-gate enablement.

Review found invalid nested quoting in the earlier canary commands. Replaced both
with shlex-generated fixed argument arrays. Tests round-trip the outer SSH argv and
inner pct argv, bind the exact payload bytes, parse Python source, and execute
only a path-substituted copy under a disposable local directory containing spaces.
No SSH/pct command is executed by any test. Cleanup rejects symlinked/non-owned/
unexpected content and avoids recursive removal. Creation fixes755/644 explicitly.

Preflight now requires exactly LoadState=not-found plus exit0 and empty stderr;
loaded/error/warning/missing outputs all reject. Unit/path names remain fixed.
No generic command/path inputs; only named fixed local child fixtures can execute.
Command proposals are immutable-by-verification and payload source hash-pinned;
changed argv or payload is rejected. This is not an external trusted run root.

Thirteen focused tests pass; full suite144 passes. Parent drains both streams using
selectors with shared8192-byte cap,1024-byte reads, independent monotonic deadline
(max20s) and bounded2s reap after kill. Tests exercise combined-stream and stderr
floods, sleeping child, closed-streams-but-live child, nonzero exit, invalid UTF8,
fixed argv/environment, exact LoadState, payload/argv tampering and local quoting.
Tiny test deadlines demonstrate timeout mechanics, not actual remote wall timing.
Child process groups are local/owned and reaped; temporary fixture paths removed.

Failure results contain a proposed exact remote-stop command plus executed=false.
This is a representation of future required fallback, not proof a remote service
was stopped. `execute_remote` unconditionally rejects even approved=true. No SSH
execution branch, user flag, arbitrary path or accepted-corpus CLI exists.

Remaining gates: technical review; separately approved mutation scope; actual
remote setup/health/cgroup/namespace validation; remote-stop integration proof;
service health recovery; full evaluator confinement and human run approval. None
is implied by these fixture tests. No dependencies or live configurations changed.

## Environment and cleanup follow-up

Review rejected self-erasure as proof of inherited-environment control. Added
fixed locale and explicit systemd pre-start unset list. Tests execute only the
AST-extracted environment prefix with invented mappings: expected key set passes,
unexpected/Python/loader/agent keys or wrong locale reject, values never appear
in output, and the environment is cleared before remaining imports/probes.
No full payload or remote worker is executed. Initial keys are not claimed safe
merely because -I or clear() was used; generic loader isolation remains unproved.

Mode tests verify creation0755/0644, reject changed directory/file permissions
without deleting either, then clean up the restored disposable fixture. These four
added tests bring the current totals to13 focused/144 full. All source, payload,
command proposal and plan hashes were regenerated after the changes.

Final independent review reproduced13 focused/144 full passing tests, verified all
current manifest hashes and clean diff, and accepted the corrected environment
and cleanup semantics for local commit only. No remote execution authorized.
