# Stream A evaluation composition — source review

Date: 2026-10-25 America/Vancouver  
Decision: **GO after dependency-closure correction; revised inactive installation pending**

## Scope

The platform branch adds the last source boundaries needed to compose the
future D4 candidate-H plus M3 evaluation without exposing private answer or
NLU content to Proxmox: fixed current-cycle F2/F3/F4/F5/admission evidence
loading, guest-local D4 and M3 structural verification, a content-free host
adapter, restored F2 schedule and evaluation-child checks, and one no-CLI
fixed-dependency composition root.

Implementation commits are `d738488c`, `00c975eb` and `85c30e44`; the original
inactive install card was platform commit `62e1eb6f` at
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

Independent review accepted both corrected boundaries. The original complete
focused macOS suite passed 94/94. No receipt, lease, timer arm, service stop, private
artifact read or model request occurred.

## Live target preflight

Read-only Proxmox inspection found eight new host composition files absent,
the current restore observer at expected SHA-256 `70748eb1…f1d3`, and both
guest files absent in LXC104 and LXC110. All five F6 units are disabled and
inactive, the whole-host lease is exactly ready, and evaluation state and locks
are absent.

Independent review initially accepted the exact 13-path inactive card: nine Proxmox
paths (eight additions and one replacement) plus two additions in each guest.
It checkpoints the replaced observer, records all twelve absent paths, runs
the then 94-test Linux suite, checks both guest wrappers inert, and rolls back only
measured paths.

## Pre-install dependency-closure correction

The final target inventory prevented an invalid installation: neither LXC104
nor LXC110 contains the host-only `evaluation_lease.py` module, but the guest
outcome verifier imported two constants from it before reaching its inert
gate. Installing `62e1eb6f` exactly would therefore have failed the mandatory
guest check and rolled back.

Platform commit `37452660` makes the two-file guest packet dependency-closed by
pinning those two immutable release identities in the pure verifier. A source
test requires them to remain equal to the host lease contract. The revised
suite passes 95/95 locally and from a clean commit archive on Proxmox. Temporary
two-file copies in each guest, with an empty `PYTHONPATH`, returned the exact
canonical disabled result and created no bytecode. All temporary files were
removed; no target installation or runtime effect occurred. Platform commit
`8e6ed141` records the revised card and successful target preflight.

Jason approved that revised installation, but the mandatory installed import
found a second dependency-boundary defect: the check exposed only the
composition directory, while the evidence loader reuses pinned modules in the
installed parent directory. The transaction rolled back. Platform record
`770af438` preserves the failure, checkpoint and successful production/F2
postchecks. No live evaluation effect occurred.

Platform commit `b21a6227` removes the remaining guest-only import from the
host outcome verifier. The V3 card at `4d682e6f` pins both exact installed
module roots and every unchanged support-module hash. Its clean archive passed
96/96 tests on Proxmox, and the temporary nine-file composition imported
successfully against those two roots without installation or bytecode.

## Remaining gates

1. Jason's fresh exact approval for the V3 reversible 13-path inactive
   placement; both earlier approvals are consumed and their packets may not be
   retried.
2. Installed hashes/custody, rollback checkpoint and unchanged-live-state
   proof; target-Linux source and isolated guest tests already pass.
3. Fresh successful F2, then F3/F4/F5/admission evidence.
4. A separate F6 arm/live-run card and approval before any consumer stop or
   model request.

This is a code-readiness milestone. It does not make the timed evaluation GO.
