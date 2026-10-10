# Minimal S0 launcher and isolation readiness — candidate for review

Status: **NO-GO for accepted-corpus execution in the current environment**.
This is a concrete design plus harmless primitive tests, not a live launcher.
No accepted corpus was accessed, fitted, scored or evaluated in this step.
The fixture-only live gate remains unconditionally disabled. No dependencies,
VMs, services, permissions, production changes or remote writes were introduced.

## Local evidence and choice

Observed host: Darwin25.6.0 arm64, existing project Python3.12.14. PATH lookup
found `/usr/bin/sandbox-exec` and system Python, but no docker, podman, colima,
limactl, bwrap, unshare, timeout or gtimeout. This proves only PATH availability,
not that packages or suitable external hosts do not exist elsewhere.

The previous harmless sandbox-exec invocation of `/usr/bin/true` with deny-network
and deny-process-fork policy returned exit71, `sandbox_apply: Operation not permitted`.
No weaker policy, elevated retry or workaround was attempted. A parent timeout
cannot supply the missing network/filesystem/process authority boundary.

Recommended minimal implementation, **only in an execution context where the
required OS profile is independently proven**: stdlib parent supervisor plus
one isolated Python worker, using existing runtime and no new daemon. Keep work
here at fixture/design readiness. First candidate is a separately reviewed local
execution context capable of applying an OS profile; whether such a permitted
context exists is UNKNOWN. A pre-existing disposable offline Linux test guest is
an alternative only after inventory and separate scope approval. Do not install
container tooling or add hardware for this small experiment. Do not silently use
an ordinary host subprocess, remove network controls or change current sandboxing.

## Verified versus blocked controls

| Control | Evidence / status | Practical limit |
|---|---|---|
| Isolated Python startup | VERIFIED: fixture child `-I -S -B` flags | Does not deny filesystem, network or system calls |
| Explicit inherited environment | VERIFIED with correction | macOS injected `__CF_USER_TEXT_ENCODING`; child removes it before evaluator import; other unexpected keys reject |
| Parent wall timeout | VERIFIED on constant sleep fixture; own process group killed/reaped | Not yet a full launcher; process-group escape requires OS child/exec denial |
| Child file-size limit | VERIFIED1024-byte RLIMIT_FSIZE fixture | Applies regular files, not pipe volume or total disk use |
| Parent pipe-output bound | VERIFIED retains at most1024 bytes and kills test child | Future worker stdout/stderr must both be drained/bounded; test probes stdout only |
| Exclusive run identity | VERIFIED atomic mkdir refuses duplicate directory | Must not auto-delete stale ownership or retry under a new ID |
| Atomic same-directory final rename | VERIFIED with fsync of temporary file | Directory-fsync/power-loss persistence not established; not a backup claim |
| Interrupted marker interpretation | VERIFIED synthetic running-without-result => unverified | No actual parent-kill/host-crash durability test yet |
| Network/child-process denial | BLOCKED in current nested sandbox | No production corpus run until an OS profile is proven |
| Input/source/runtime read-only confinement | UNKNOWN | File modes under same UID are not a security boundary |
| Hard CPU/address-space limits | Constants available; behavior UNKNOWN | Resource constants alone prove neither enforcement nor RSS equivalence |
| Hard256MiB RSS ceiling | UNKNOWN | RLIMIT_AS is address space, not RSS; do not label it an RSS guarantee |
| External frozen root / runtime digest | PROPOSED, not established | Writer-generated manifest alone is not independent authorization |
| Atomic bounded interrupted evidence | PROPOSED | Existing tests validate primitives, not complete crash/restart behavior |

Six new primitive tests pass; full adaptive suite131 passes. An initial environment
probe failed because the OS added a key; retained as a finding, then corrected by
explicit bootstrap removal. Tests use constant invented children in disposable
scratch folders; never evaluator source or accepted cases in a child. Every child
is reaped; no listener, scheduled job or persistent process remains.

## Concrete future launcher contract

Proposed module: `scripts/aster-adaptive/s0_isolated_launch.py`, **not created**.
No generic command option. One reviewed fixed worker entry point; no eval, plugins,
network libraries or environment-selected Python executable. Parent owns all
process creation. Approved invocation identifies a frozen run manifest and a
pre-existing approved scratch root; it does not accept arbitrary input paths.

Frozen manifest must bind run ID, exact plan, nine evidence artifacts plus summary,
source, adapter, worker and launcher hashes, Python executable/standard library
inventory, OS/architecture and immutable isolation profile. All paths canonical,
regular, non-symlink, expected owner; reject path traversal, duplicate records,
changed bytes and unexpected files. The independently reviewed root digest is
provided outside the writable worker bundle and recorded with explicit human run
approval. This is provenance, not proof of a cryptographic human identity. The
parent copies once, hashes the copied bytes, and exposes that same snapshot read-only.
No check-path-then-reopen race or caller-regenerated trust root.

Worker setup must precede loading pinned routing code: isolated Python bootstrap,
expected environment validation/scrub, resource limits, verified OS restriction and
opened permitted descriptors only. OS policy allows only the pinned runtime/bundle
reads and parent-controlled IPC; denies network including local model/Unix sockets,
process fork/exec/spawn after initial worker startup, unrelated file reads/writes,
IPC access to services, executable writes and privilege escalation. Exact profile
syntax is deliberately not invented without a working execution environment.
Negative fixture probes must prove socket creation/connect, fork/spawn and reads
outside allowlisted roots fail; deny tests use disposable targets and no private files.

The parent has a strict allowlist too: no remote credentials/environment copied,
no corpus text in diagnostic errors, no network or arbitrary shell capabilities.
Parent creation of the one worker is separate from the worker's denied child-process
capability. OS termination of the worker cannot grant any production authority.

## Bounds and parent/worker protocol

- One exclusive `run-<frozen-id>` directory, mode0700, created with atomic mkdir.
  Existing ID always refuses; stale state is inspected, never silently overwritten.
- Parent records `claimed` then `running` with hashes and monotonic start/deadline,
  before starting worker. State contains metadata, not credentials or raw prompts.
- Wall deadline60 seconds for initialization plus entire experiment; parent enforces
  it independently of worker progress and uses a monotonic clock. CPU limit provides
  an additional tested ceiling where supported, not a replacement for wall time.
- Worker accepts exactly30/20/10 with one dev family per stratum, matching approval
  hashes, unique family IDs and agreed profiles. Only20 train targets reach fitting;
  dev text reaches prediction; labels remain in scoring. No arbitrary corpus glob.
-60 initial decisions (3engines ×2profiles ×10dev);30 repeated timing passes each.
  Deterministic ordering/ties, fixed0.2 threshold, no fitting or retries on dev scores.
- Parent drains stdout and stderr with selectors, bounded chunks and combined2MiB
  cap. Worker framing is length-prefixed with a small fixed header; declared or actual
  oversize aborts. No unlimited communicate(), accumulated stderr or partial success.
- RSS observed in normalized units. A separately verified memory containment primitive
  must bound allocations; if exact RSS cap cannot be enforced, do not silently claim
  compliance. Present a concrete budget amendment before execution, or remain blocked.
- Timeout/limit/protocol failure: record failure, kill owned process group, reap,
  preserve already validated bounded progress and mark unprocessed cases failed.
  Never count a missing record as agreement or remove it from denominator.

## Output and recovery lifecycle

States: `claimed -> running -> complete|failed|timed-out|output-limit|interrupted`.
A worker cannot write final state. Parent checks exact row set, status/capability
schema, predictions, metrics recomputation, full reference digests and finite resource
values before success. Preserve bounded raw prediction records and failures. No
promotion, registry writes, policy edits or automatic Git staging exists.

Use exclusive O_NOFOLLOW files under parent-owned run directory, temp file and
same-directory rename after validation/fsync; fsync directory where supported and
test its semantics rather than claiming power-loss durability. Final record includes
input/runtime/plan/output hashes. Worker writes only through pipe, not result paths.

If parent dies or restarts with `running`, treat result as interrupted/unverified.
Do not blindly kill a recorded PID (PID reuse): verify owned process identity before
any cleanup. With worker fork/exec denied, no detached descendant may survive; an
additional parent-liveness mechanism/OS job containment must be tested. No automatic
rerun. Report incomplete evidence and ask for a new bounded run decision if needed.
Interrupted records never masquerade as a complete benchmark.

## Next readiness test matrix (fixtures only)

Before a proposed live run: prove OS negative network/process/filesystem tests;
blocked environment key/secret inheritance; modified pinned source/runtime/input;
empty/duplicated/missing family set; duplicate run ID; hung worker; output flood on
both streams; invalid UTF8/frame/JSON; file/symlink race; memory/CPU overrun; worker
crash before/after header; parent kill and restart; partial evidence; deterministic
recovery; accepted-output atomicity; failed final hash/metric validation.

Current primitive tests are groundwork, not substitutes for those integration
checks. Never use accepted cases to troubleshoot a launcher. No fixture may contain
real secrets or real private paths; use planted non-secret denial targets.

## Review gate and rollback

Technical review this design and primitive tests before local commit. Next proposal
must identify a permitted concrete execution context and isolation mechanism; no
sandbox escalation or host mutation is implied. Actual corpus launch requires a
fully pinned candidate, proven controls and exact human run approval. Until then
`require_live_readiness` continues unconditional denial and plan live pins remain null.

Rollback now: remove unused candidate test/design if rejected; retain review history.
No live system or identity depends on this work. No deployment, new dependency,
accepted-corpus access, live-gate change, installation or push is authorized here.

Independent technical review reproduced all6 primitive and131 full tests, verified
the manifest and accepted this design for local commit only. This does not change
the current-environment NO-GO or authorize a live launcher/corpus run.
