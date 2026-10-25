# M1 web read-only passkey-session candidate — 2026-10-25

## Decision

**READY FOR A SEPARATELY APPROVED ONE-FILE INSTALLATION.** The existing web
Companion can display the approval session, but it has no effect-free way to
obtain a fresh passkey claim. Its only fresh-authentication continuations lead
to a Red approval or management action. The installed Mac Companion cannot
safely fill this gap because its available signing identity differs from the
installed R2 identity.

This candidate adds one web control, **Verify approval session with passkey**.
It enters the existing mandatory passkey flow and, after return, performs only
the existing read-only approval-session and management reads. It never submits
an approval, management action, capability grant or model request. Unknown
saved continuation kinds now fail closed rather than falling through to the
broker-action function.

## Live-source boundary

The live LXC104 `aster_agent.py` is not byte-identical to this branch. It
contains the production OpenBao controls and knowledge-usage integration while
this branch contains later unrelated source changes. Replacing the whole live
file from the branch would therefore be unsafe.

The reviewed deployment artifact is the exact three-hunk patch
`services/aster-agent/m1-read-only-passkey-session-20261025.patch`:

- live baseline: `7edc7ff9776357d62f6eff45de2093aab5749bb38317251b404df88012c6b50c`
  (`147074` bytes);
- patch: `f342f5545d8a8bd138f57812958cd12a9f4e7df1a3b89cbfcbf7827f9fd9166d`;
- exact derived candidate: `007a61dee8daa430dc041e915250532ab1bdabf01166d2e7b44eec189e9fe88e`
  (`147745` bytes).

Applying the patch with zero fuzz to a fresh copy of the observed live baseline
reproduced the candidate byte for byte. Any baseline or output mismatch is a
hard stop.

## Offline verification

- Python syntax compilation passed for the repository source and the exact
  live-derived candidate.
- The new continuation test passed against both sources. It proves that the
  session-check continuation calls only `loadManagement`, that effect functions
  remain uncalled and that an unknown kind fails closed.
- The rendered production-candidate JavaScript passed all seven Companion
  voice tests.
- The broader browser notification suite passed all eleven tests.
- The existing fresh-login test passed, preserving mandatory Authentik flow,
  same-origin OAuth continuation, PKCE and management-action custody.
- Python approval-service tests could not run in the bare Mac system Python
  because its optional FastAPI/JWT dependencies are absent. The installation
  gate therefore requires the existing target environment suite before any
  restart.

## Exact installation gate

Before installation, re-read the live file and require its exact baseline hash,
root ownership, mode `0644`, active `aster-agent.service`, healthy Aster and an
empty approval effect queue. Preserve the exact original in a new root-only
rollback directory. Apply the pinned patch with zero fuzz to a staging file,
require the exact output hash, compile it and run the focused browser tests plus
the target approval suite. Install only that file, restart only
`aster-agent.service`, and verify:

1. service and Aster health;
2. unauthenticated approval-session denial;
3. ordinary signed-in read-only web state;
4. unchanged broker database hash and zero pending or approved-unconsumed
   requests;
5. a supervised passkey session check that produces no approval, management
   action, capability change or model call.

Any failed or uncertain check restores the exact checkpoint and repeats the
health and database checks. This card does not authorize installation, a Red
approval, a management change, a capability grant, a model call, Mac app
replacement or routing promotion.
