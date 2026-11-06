# AsterTV v3 M10 — reviewed reference and mirror intake candidate

Date: 2026-11-05

Status: local candidate complete; remote synchronization and live intake remain pending

## Reviewed operational reference

The existing `homelab-reference` repository now has a dedicated
`operations/astertv.md` page at local commit
`62bb587aa692b84d6c672c717e43daa1d0b4a432`. It records:

- the four-member lifecycle matrix without claiming Guest is deployed;
- Family's Dolby/HDR/equipment-control contract;
- Bedroom's Wi-Fi, stereo PCM and AC3/EAC3 contract;
- Jen's device-only 1080p-media/18 Mb/s/stereo ceiling while preserving native
  GUI resolution;
- deterministic composition, checkpoint, promotion, rollback and incident
  boundaries; and
- the current clean Bedroom/Jen Doctor and Beszel state while leaving Family
  explicitly unobserved.

The page content SHA-256 is
`5f8c3a3b13acaea93dead378ca114defac0ea74e3abdd55d61f7926a49d7da9d`.
The repository-wide reference lint passes all 18 operational pages. Two older
metadata lines were normalized to the contract's exact `Reviewed: YYYY-MM-DD`
shape without changing their factual scope. The unrelated pre-existing
`.DS_Store` remains untracked and was not committed.

## Derived-mirror intake candidate

`services/aster-wiki/source-batches/milestone-astertv-v3-m10.json` declares the
reviewed page as one bounded manual source:

- source ID `astertv-operational-reference`;
- private local-reviewed authority;
- exact file `AsterTV-Operational-Reference.md`;
- version policy `homelab-reference-commit-62bb587`;
- 256 KiB ceiling; and
- `allow-derived` mirror policy with private HomeLab licence metadata.

The manual route deliberately avoids granting LXC 113 a Forgejo credential.
The existing intake will retain the exact upload, validate it, atomically
accept it and generate provenance-linked mirror claims. The human operational
page remains authoritative; the mirror remains derived.

All 55 Aster Wiki collector/intake/mirror tests pass, including atomic
acceptance, rollback, source-scoped manual fetch, provenance verification and
deterministic mirror generation. The new batch also passes the production
manifest validator.

## Boundary and next action

No remote repository, live wiki, collector, mirror, service or appliance was
changed. Promotion requires a fresh remote-write authorization to push the
`homelab-wiki` and `homelab-reference` commits to their Forgejo origins. After
those refs are verified, publish only the 25 authored AsterTV pages and home
link into LXC 113 while preserving all 31 live collector sources and generated
pages, then enroll the exact reviewed reference through intake, run the
collector, build and verify the mirror, and refresh the content-free M10
observation.
