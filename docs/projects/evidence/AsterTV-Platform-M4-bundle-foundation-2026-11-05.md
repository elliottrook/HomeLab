# AsterTV Platform M4 bundle foundation evidence — 2026-11-05

## Outcome

The release planner now constructs byte-deterministic, hash-bound composition
bundles from the verified v2.0.7 base and the exact source inventory for every
selected overlay. Each bundle contains its canonical manifest, guard contract,
base release and ordered overlay source bytes. The guard contract includes
expected payload hashes and required external dependencies.

This is deliberately a **candidate build gate**, not a deployment approval.
Six overlays now have complete contracts: Family restart, target-aware release
guard, Bedroom Wi-Fi, Bedroom stereo assertions, Family Dolby/HDR assertions
and the target-aware Remote client. The other 12
overlay definitions name their exact current inputs and explicit blockers.
Plans therefore build successfully but remain non-deployable.

## Audit findings preserved as blockers

- Historical transformers do not yet have checked-in rendered output trees.
- Audio, HDR, Wi-Fi and several Kodi settings are assertions, not files.
- Home Assistant, OPNsense, Jellyfin and identity state require external-state
  contracts and must never be copied into a public bundle.
- Intro Skipper lacks the required SHA-256 and provenance record.
- Jen low-spec setup transforms more than 25 undeclared v2 files.
- Account, Aster client, Guest and Home installers duplicate payload ownership.
- The accepted remote-client service hash and current source need reconciliation.
- TV details is still a hotfix chain rather than one reconciled final payload.

## Verification

- Fleet/release suite: 27/27 passing, including typed assertion drift and
  target isolation.
- Four deterministic bundles build from the locally verified immutable release.
- Repeated builds are byte-identical.
- Guest stays non-deployable.
- The Family restart overlay is reproducibly rendered from exact predecessor
  members in the pinned release; its four outputs and renderer are hash-bound.
- Release-guard units are rendered with literal Family, Bedroom and Jen
  identities; no device bundle includes another device's unit.
- Bedroom's Wi-Fi unit is hash-bound to its destination and paired with the
  required disabled-power-save assertion.
- Guard contracts contain installed destinations, not repository paths, and
  the hostname-bound collector fails closed on missing files.
- The Remote client lineage conflict was resolved read-only: Family, Bedroom,
  Jen and the repository all use `0eba8fc5...`; `1a4d52f3...` is the recorded
  predecessor. Current add-on, stable copies, manifests and host-specific units
  are materialized while keys/config/database state remain excluded.
- Family, Bedroom and Jen remain blocked by their other incomplete overlay payload contracts.
- Payload and dependency drift tests fail closed.
- No live appliance, wiki, network, Home Assistant or remote repository changed.

## Next

Materialize transformer output trees from the pinned predecessor, define typed
assertions/external artifacts/mutable-state exclusions, resolve ownership, then
mark overlays complete one at a time. Only after all selected overlays are
complete may Doctor consume live sanitized observations and a device plan become
eligible for the M7 Jen rehearsal.
