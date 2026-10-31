# October31 qualification — admission passed, entry capture refused

## Actual outcome

Read-only reconciliation after the booked night finds **NO-GO before entry
checkpoint/claim/drain**. This is progress through the backup gate, not a
successful restoration qualification or a model result.

- The01:15 integrity service ran01:15:00–01:23:32 PDT, exit0. Its immutable
  terminal says `complete`, `ai_stack_effects=false`, same-cycle archive proof
  `retained-archive-integrity-sha256:96f4b3e47587da8e1c1bc7f3f858c28a3fd52f98dd42a26fe49df17c06ff445f`.
- The03:10 launcher exited0 after launching the owner; this is not success.
  The owner exited1 at03:10:30, fixed journal result `no_go/UnitStateError`.
- `admission.json` records observed epoch1793441400, whole backup verified,
  qualification-only and one accepted entry GPU holder. The installed source
  therefore passed fresh admission, including its full backup/mirror gate.
- The session directory contains only `admission.json` and `session.lock`;
  no `session.json`, `entry.json` or `adapter.json`. The guardian has no start
  timestamp. The reservation remains byte-identical `reserved`, unclaimed.
  No exclusive release record exists.
- In the exact installed source, `UnitStateError` in this path arises during
  the first unit inventory capture, before guest file checkpoint capture,
  guardian, booking claim, isolation or trial. No stack drain or model trial
  ran. This does not establish live recovery or owner-loss qualification.

No manual lease/drain/operation markers or shared-directory flock holders
were present at this reconciliation. Read-only observations of all13 exact
profile unit identities find supported current states: Agent104, inference110,
News UI114, Paperless broker115 and Speech116 active; declared timers active;
News/Paperless static workers inactive; narration116 activating with PID/tasks.
These are current observations, not a reconstruction of03:10 state or an
authenticated complete production health test. No health/model request ran.

## Exact retained source receipts

Paths below are on Proxmox; SHA-256 covers actual file bytes.

| Path | SHA-256 |
|---|---|
| `/var/lib/local-ai-lab/exclusive-integrity/b60-exclusive-20261031/terminal.json` | `e057efd5949b94dd42e92a25b8d3fb48fd588df8bf38d2e5e3549b35719f6b8c` |
| `/var/lib/local-ai-lab/exclusive-sessions/b60-exclusive-20261031/admission.json` | `4e81d8f9d8bb9d13772b2312b877722ee1960ef8f1e7df946228f38e7900bf40` |
| `/var/lib/local-ai-lab/reservations/records/b60-exclusive-20261031.json` | `9ca18763b854ec6800a9431dafae9c26a3bec381955f0fc38ff636ed7fe34d1f` |

The installed old source closure and activation remain those pinned by
[the arming receipt](qualification-armed-20261031.md); this heartbeat did not
install, arm, change timers, acquire a lease, stop services or touch recovery
bytes. No expired booking was replayed.

## Demonstrated observability gap and offline candidate

The deployed CLI deliberately reports only the exception type for
`UnitStateError`. It discarded the specific constant that would distinguish
failed/malformed/unsupported unit observations, unstable entry and deadlines.
Current unit rows pass the supported shape, but cannot prove the historical
cause. Do not label this a timer, narration, timeout or systemd defect without
the missing evidence; do not relax stable-entry or observation checks.

Implementation commit `d7af148021190cf0fcaaca861bb415461802b554` adds only an
explicit allowlist of unit failure constants at the CLI journal boundary.
Unknown unit error strings become `UNIT_FAILURE_UNCLASSIFIED`; untyped errors
still expose only their type. No retry, admission, observation, recovery or
effect behaviour changes. Four new tests exercise every reviewed constant,
unknown/newline redaction, untyped redaction and one nonzero CLI attempt.

Candidate CLI SHA-256:
`64f7e5458ccc93b2754e3196ddcab4bda4a094c759c7a0f2a8174d173a627d02`.
Published reproducible patch:
`scripts/b60-inference/unit-diagnostics-20261031/0001-Expose-allowlisted-exclusive-unit-refusal-codes-with.patch`,
SHA-256 `218593a63f7ace7f0520756f915d5a432eda887a7d627bb94a57f72c72c733fd`.
Apply after existing full implementation through `56cd9c35c`, including the
prior undeployed backup diagnostic candidate. Independent replay tree equals
implementation tree `dfeb72eb92c25893ce1470e827758b2fd0c23511`.
134 Lab Hours tests and107 B60 tests pass against that exact replay, no skips.
These are offline/fake-effect tests, not live qualification. The candidate is
**not deployed** and must not be copied over the old source/profile pins.

## Peer receipts and next action

Authoritative Forgejo refs fetched and their current records read:

| Ref / exact commit | Path | SHA-256 |
|---|---|---|
| `codex/aster-stream-a-handoff` / `d88f8239b6771836c3e56c59229db81a8c18ddd6` | `docs/projects/AI Projects/evidence/SA3-expanded-source-quality-inactive-install-preflight-2026-10-29.md` | `f4f72df5d792f17ce11ec87aae69e856f83865cac5b31b08146c65c32e8ac94a` |
| `codex/b60-adaptive-coordination` / `3cf7035e75701b451f91aa052d170521d1a31203` | `docs/projects/B60-Inference-Engineering/qualification-armed-20261031.md` | `67b174cd29def0e599f522787c13410441aa3d5f4e28523f1a8325730268ba73` |
| `codex/release-registry-stream-a` / `6fb0207fec5190e0c34ed3bc72ea38e128f06127` | `docs/projects/Local-AI-Platform-Split.md` | `6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7` |
| `codex/aster-lab-hours-booking` / `5a9c3471398cfeecc0c6db35bfb264f87d8318f9` | `services/local-ai-lease/ASTER-LAB-HOURS-RESERVATION-RUNBOOK.md` | `ed990e68fe04e4c238c192ff94fc81b275cf6cf622c0004e55afb26edda047ba` |

No new peer response; SA3's separate dormant install remains distinct from
this B60 owner. GitHub read-only protection ref matched `3cf7035e7` before
publication; publication does not prove peer reading.

Next operational continuation: review/build a fresh exact diagnostic closure,
check real shared-owner release, prepare source-bound future metadata/profile
and date-specific integrity/qualification under the next valid reserved
booking. It must establish a specific unit refusal or complete normal
restoration before owner-loss qualification and candidate/mount/resource
extension. Capacity reservations alone do not dispatch future nights. No
future activation is claimed by this preparation-only turn, and there is no
new human approval dependency for ordinary in-scope Stream A work. The
operational continuation must use its own authorised execution context, not
silently turn this restrictive heartbeat into an installer. Keep the
programme active;27B+ reasoning/latency success remains unproved.
