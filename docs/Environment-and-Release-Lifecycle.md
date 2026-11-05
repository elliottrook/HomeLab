# HomeLab environment and release lifecycle

> Status: adopted authority
>
> Owner: Jason
>
> Adopted: 2026-11-05

## Purpose

This document is the repository authority for the distinction between an
environment, a release, a deployment and a device-specific composition. It
restores the lifecycle prerequisite referenced by the project portfolio and
implements the HomeLab Project Creation Standard's lab/release/production
rules. Service-specific projects may tighten this contract but may not silently
weaken it.

## Terms

- **Environment** is an operational role and trust boundary such as disposable
  development, lab, accepted baseline or production. It is not a branch name.
- **Candidate** is mutable work under evaluation. It is not a release.
- **Release** is immutable identified bytes, an exact Git commit, checksums and
  a reproducible manifest of code, dependencies, schemas and material assets.
- **Composition** is a release plus approved profiles, overlays, external
  contracts and opaque credential references for one target.
- **Deployment** is the recorded act of installing one accepted composition on
  one identified target.
- **Lab baseline** is the sanitized retained copy of an accepted release for
  recovery and comparison. It is not a writable production mirror.
- **Observed state** is a dated sanitized report. It cannot become desired state
  merely because it exists live.
- **Overlay** is a named, compatible, independently owned change above a base
  release. An emergency edit is not an overlay until reconciled and accepted.

## Lifecycle states and channels

Asset lifecycle states are `candidate`, `lab`, `accepted`, `production`,
`degraded`, `retiring` and `retired`. Release channels are separate:

1. `development`: mutable source and synthetic fixtures;
2. `lab`: a candidate installed only on a declared lab target;
3. `accepted`: frozen bytes and manifest that passed review and recovery gates;
4. `production`: an accepted composition promoted to a production target.

A production target may run an older accepted release. A lab target may run a
production release plus lab-only overlays. Neither fact changes the lifecycle
meaning of the target or release.

## Authorities

| Fact | Authority |
|---|---|
| Source and desired composition | Git project/fleet contract |
| Immutable release bytes and checksums | Private Forgejo release |
| Device/interface/IP/VLAN/cabling | NetBox |
| Current deployed state | Sanitized live query, recorded as observation |
| Reviewed current operation | `homelab-reference` |
| Human guidance | Existing private `homelab-wiki` |
| Secret value | Existing custodian/source-local file, never Git/wiki |
| Decision and evidence | HomeLab project record |
| Derived Aster knowledge | Aster mirror, never authority |

An authority disagreement is drift to investigate. Lower-authority evidence
must never overwrite a higher-authority record automatically.

## Candidate to production

1. Create or update a candidate in the declared lab environment.
2. Compile the complete target matrix, including inactive candidates whose
   compatibility matters, and fail on ownership/dependency conflicts.
3. Run unit, schema, malformed-input, secret-pattern, regression, performance
   and recovery tests proportional to the change.
4. Freeze the candidate as a Git commit and immutable release manifest. Record
   every dependency/schema/material asset digest and the supported target set.
5. Review the composition diff for every affected device. A global release may
   not erase a room, hardware, peripheral, audio, network or recovery overlay.
6. Check idle/playback state, target identity, checkpoint and rollback before a
   deployment. Stop on mismatch or unexplained drift.
7. Promote incrementally from lab to the lower-risk production target, soak,
   then continue to the higher-impact target. AsterTV uses Jen lab, then Bedroom,
   then Family unless an accepted project records a narrower order.
8. Validate intended behavior and collateral behavior, not just process exit.
9. Record observed hashes, evidence, rollback and operator handover. Retain a
   sanitized lab baseline independent from production secrets and mutable data.

Remote Git synchronization, tags and Forgejo releases remain separately gated
by repository rules even when a project is Stream A.

## Overlay and exception rules

- Reusable behavior belongs in the base release or a reusable profile.
- A one-device exception requires an owner, reason, compatibility, tests,
  rollback reference and review/expiry decision.
- One resource has one owner in a layer for any composed target.
- Dependencies are explicit and acyclic; missing/incompatible inputs fail.
- Every active target compiles before a global release can be accepted.
- Overlay order is dependency-derived, never filesystem or conversation order.
- Emergency live repair restores service first, then enters the contract as a
  reviewed overlay or is rolled back. It never silently becomes the baseline.

## Secrets and mutable data

Release/composition manifests may contain only opaque custody identifiers.
Passwords, tokens, private keys, credential hashes usable for authentication,
account content, watch/listen history, camera frames and typed text are
forbidden. Source-local credentials and mutable state are checkpointed and
restored by their own service contracts, never copied into a release.

## Compatibility and retirement

Each release declares supported OS/runtime/API/schema ranges and each overlay
declares compatible releases and targets. A deprecated release records support
end, replacement, security disposition and tested rollback/export. Retirement
requires proof that no target or recovery procedure depends on it; immutable
evidence may remain even after live bytes are removed.

Hardware constraints are scoped to their measured profile. AsterTV-Jen's
1080p/stereo qualification is not a limit on the AsterTV platform.

## Recovery and failure behavior

- Preserve the last-known-good release, per-target composition and checkpoint.
- Deployment is atomic or transactionally reversible; partial output is not
  presented as accepted.
- A failed identity, idle, compatibility, hash, health or rollback check stops
  promotion and leaves the previous accepted composition in service.
- Restore must work without the wiki, Aster or the original implementation
  agent. Restore evidence names order, dependencies and the tested result.
- Observed drift is reported; automatic repair is limited to the accepted
  composition and must exclude credentials and mutable application state.

## Required release record

An accepted release records at minimum:

- release ID, source commit and creation date;
- artifact name, size and SHA-256;
- code, dependency, schema and material-asset versions/digests;
- supported targets and compatibility ranges;
- included/excluded mutable data and credential boundary;
- test matrix, SBOM/license/security review status;
- migration, checkpoint, rollback and restore proof; and
- known limitations, support owner and deprecation status.

The AsterTV implementation is `services/kodi/astertv-fleet/`. Its canonical
YAML-1.2 JSON-subset manifests and deterministic compiler produce per-device
desired manifests and the human-readable release matrix. Those generated files
are inputs to later deployment/Doctor milestones; M1 performs no deployment.

