# D3 native refresh observed; current Companion build changed

**Read-only observation, 2026-10-12.** No Companion launch, sign-out, token
inspection, Keychain read, Codex question, tool grant or app replacement was
performed for this check. The limited routine Ask Codex release remains
**HOLD** pending reconciliation of the current installed build and its normal
use. This record does not change the v16 historical test result.

## Natural refresh provenance

A bounded macOS unified-log query selected only subsystem
`com.elliottrook.aster-companion`, category `session`, and the seven fixed
allowlisted refresh codes. Its output to this record contained only those
codes, timestamps, process names/IDs and a Boolean executable-UUID comparison;
no raw log text, token, subject, expiry, request or answer was printed.

From 09:21 through 17:31 Vancouver time, the `AsterCompanion` process with
PID 26994 emitted nine `refresh_started` events, each followed by
`refresh_succeeded_persisted`. All nine success events' process-image UUIDs
match the retained signed version-16 executable at
`/Applications/AsterCompanion.pre-openbao-20261012.app`, whose SHA-256 is
`06eab741db94718ac5eb8ae7c270da3b3423467ca40a9fa4e737b84f4236ebff`.
The same log window contained `xctest` refresh/cancellation events; they were
excluded from the app result. This establishes that the installed v16 app
entered the natural refresh branch repeatedly and its Keychain save reported
success. It does **not** prove a later independent Keychain read after process
restart, that no macOS prompt appeared off-screen, sustained provider
availability, or answer quality. The earlier ordinary-use observation records
Jason's one first-launch prompt and no repeat in two read-only UI checks.

## Changed installed artifact

A later read-only check found `/Applications/AsterCompanion.app` modified at
18:51 Vancouver time. It is signed and passes strict/deep verification, but
its current `CFBundleShortVersionString` is `0.2.2`, build `4`, executable
SHA-256 `7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`:
different from the observed v16 binary. The computer-use app inventory did
not list the current bundle as running. The owner, purpose, source commit,
rollback and normal-use behavior of this replacement are
**UNKNOWN / REQUIRES VERIFICATION**. A platform-agent coordination message
requested its provenance. Do not launch it merely to force this gate, revert
another project's app, or read Keychain material.

## Decision

The **v16 natural-refresh subgate passes** on executable-bound, fixed-code
evidence. The **current installed-build release gate remains HOLD** until the
new build's ownership, source/signature/rollback and ordinary authenticated
use are reconciled. Neither result enables automatic routing, connected
tools, AI-PAM Stage 2 or a sysadmin role. Preserve the retained v16 and v15
copies while the installed build is reconciled.
