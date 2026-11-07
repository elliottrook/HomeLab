# AsterTV platform M2 live wiki publication — 2026-11-07

## Outcome

The accepted AsterTV department content from private `homelab-wiki` commit
`973600d4cce5aab75ef7a21eba186755db8110bd` is live on LXC 113. The
publication replaced only the operator-authored `docs/astertv` subtree. It did
not change collector sources, accepted locks, retained originals, generated
upstream pages, the derived Aster mirror, credentials, ingress or network
policy.

The live department now contains 27 Markdown pages. Its concatenated sorted
page digest is `11bddc81a818f77b00b85289d3706b9f9d12a0462ab88aa5e2578019ea8df21d`.

## Preflight and custody

- Exact target: LXC 113, hostname `aster-wiki`, `192.168.20.34`.
- Intake service: active, PID 88, zero restarts.
- Collector service: inactive/dead before publication.
- Existing accepted-source verification: 33 checked, status `ok`.
- Candidate Git archive:
  `3ddafc07b0ae50b171a7d4befd16c103d102c76fdf2c347fa831c612cd706e62`.
- The archive hash matched on the Mac, Proxmox and inside LXC 113.
- In-container candidate validation passed 3/3 tests and all 27 pages.
- Filesystem headroom was 14.4 GB available.

## Transaction and rollback

The named recovery checkpoint is:

`/var/lib/aster-wiki/state/checkpoints/astertv-authored-973600d-20261107`

It retains the exact 25-page predecessor twice as `astertv.recovery` and
`astertv.pre-attempt2`, plus `before.sha256.json`. The first atomic attempt
correctly restored the predecessor when a publication probe expected the wrong
page title. No invalid candidate remained live. Inspection proved the candidate
heading was `AsterTV engineering: start here`; the content and local validation
were not defective.

The second attempt atomically renamed the same-filesystem staged 27-page tree
into `docs/astertv`. It preserved owner `aster-collector`, group `aster-wiki`,
setgid directory custody and mode-`0640` files. The intake service required no
restart.

Rollback is a same-filesystem rename of the current subtree out of the way and
either retained predecessor back to `docs/astertv`, followed by the same local
HTTP and source-verification checks.

## Post-publication validation

- `/healthz` returns status `ok`.
- AsterTV Start Here renders with the exact expected heading.
- The new household guide and promotion/rollback pages render through the live
  application.
- The live tree is byte-identical to the Git candidate.
- Accepted-source verification remains 33 checked, status `ok`.
- Intake remains active on PID 88 with zero restarts.

The full corpus-health command separately reports that the mirror accepted-
input state differs from the human accepted lock. It also reports two stale
sources, but zero broken links, directory-index drift, duplicates or
unclassified sources. The retained production report from 2026-11-06 had 32
sources and no mismatch; the current accepted set has 33. This authored-only
publication did not change either accepted-lock or mirror state and did not
attempt to repair that independent mismatch. Derived-mirror reconciliation
therefore remains open and must follow its own authority and checkpoint.

## Next boundary

The human AsterTV wiki is published. The derived Aster mirror is not yet
reconciled to the current 33-source accepted lock. Appliance promotion and
Bedroom equipment/volume acceptance remain separate AsterTV v3 gates.
