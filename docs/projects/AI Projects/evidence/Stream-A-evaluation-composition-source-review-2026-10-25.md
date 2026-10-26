# Stream A evaluation composition — source review

Date: 2026-10-25 America/Vancouver  
Decision: **GO for source-only composition; inactive installation pending**

## Scope

The platform branch adds the last source boundaries needed to compose the
future D4 candidate-H plus M3 evaluation without exposing private answer or
NLU content to Proxmox: fixed current-cycle F2/F3/F4/F5/admission evidence
loading, guest-local D4 and M3 structural verification, a content-free host
adapter, restored F2 schedule and evaluation-child checks, and one no-CLI
fixed-dependency composition root.

Implementation commits are `d738488c`, `00c975eb` and `85c30e44`; the reviewed
inactive install card is platform commit `62e1eb6f` at
`services/local-ai-lease/STREAM-A-EVALUATION-COMPOSITION-INACTIVE-INSTALL-CARD-20261025.md`.

## Findings and corrections

The first independent review rejected two gaps. The public builder exposed
test injection points that could replace production paths, UID, runner or
clocks, and F2/F3 were validated separately without direct row equality. The
correction removed all operational overrides from the public builder and now
requires exact ordered equality of the three F2/F3 archive identity, timing
and exit rows before admission.

The guest verifier was then made inert by default. It reads no artifact unless
the fixed host command supplies both one allowlisted workload and
`--verify-authorized`. Its success output is limited to schema, workload name,
journal digest, result digest and call count; the host supplies the separately
measured elapsed time.

Independent review accepted both corrected boundaries. The complete focused
macOS suite passes 94/94. No receipt, lease, timer arm, service stop, private
artifact read or model request occurred.

## Live target preflight

Read-only Proxmox inspection found eight new host composition files absent,
the current restore observer at expected SHA-256 `70748eb1…f1d3`, and both
guest files absent in LXC104 and LXC110. All five F6 units are disabled and
inactive, the whole-host lease is exactly ready, and evaluation state and locks
are absent.

Independent review accepted the exact 13-path inactive card: nine Proxmox
paths (eight additions and one replacement) plus two additions in each guest.
It checkpoints the replaced observer, records all twelve absent paths, runs
the 94-test Linux suite, checks both guest wrappers inert, and rolls back only
measured paths.

## Remaining gates

1. Jason's exact approval for the reversible inactive placement.
2. Target-Linux tests, installed hashes/custody, rollback and unchanged-live-
   state proof.
3. Fresh successful F2, then F3/F4/F5/admission evidence.
4. A separate F6 arm/live-run card and approval before any consumer stop or
   model request.

This is a code-readiness milestone. It does not make the timed evaluation GO.
