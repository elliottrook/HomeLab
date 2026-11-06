# AsterTV Platform M4 bundle foundation evidence — 2026-11-05

## Outcome

The release planner now constructs byte-deterministic, hash-bound composition
bundles from the verified v2.0.7 base and the exact source inventory for every
selected overlay. Each bundle contains its canonical manifest, guard contract,
base release, ordered overlay source bytes and a normalized install tree for
every owned destination. Install members retain declared modes, are resolved
from reviewed hash-matched sources and reject destination escape or duplicate
ownership. The guard contract includes expected payload hashes and required
external dependencies.

This is deliberately a **candidate build gate**, not a deployment approval.
All eighteen overlays now have complete contracts: Family restart, target-aware release
guard, Bedroom Wi-Fi, Bedroom stereo assertions, Family Dolby/HDR assertions
the target-aware Remote client, the reconciled TV-details tree, and target-aware
News playback, Family media lifecycle, the Family equipment bridge, and Jen's
immutable account-registry code, Jen's immutable Aster client, and Jen's exact
News icon overlay, Jen's podcast-request surface, and Jen's Guest catalogue
adapter, Jen's composed Home/Cameras surface, and its composed Movie/YouTube
surface, and the Jen low-spec runtime.
All overlay definitions name their exact current inputs and explicit blockers.
All three deployed-device plans build successfully and are eligible for a
future promotion transaction. No promotion was performed.

## Audit findings preserved as blockers

- Historical transformers do not yet have checked-in rendered output trees.
- Audio, HDR, Wi-Fi and several Kodi settings are assertions, not files.
- Home Assistant, OPNsense, Jellyfin and identity state require external-state
  contracts and must never be copied into a public bundle.
- Intro Skipper lacks the required SHA-256 and provenance record.
- Jen low-spec setup transforms more than 25 undeclared v2 files.
- Aster client, Guest and Home installers still duplicate payload ownership;
  the account registry now owns the shared immutable account code explicitly.
- The accepted remote-client service hash and current source need reconciliation.
- Shared family-manifest state must remain an assertion/merge surface rather
  than being copied from one appliance over another.

## Verification

- Fleet/release suite: 41/41 passing, including typed assertion drift, target
  isolation, install-path containment and fail-closed missing/stale/drifted
  observation handling.
- Four deterministic bundles build from the locally verified immutable release.
  With normalized install trees, the current artifact hashes are Bedroom
  `0fa9c015...c253`, Family `bd20c352...5cbd`, Guest candidate
  `4d79b20a...1e0`, and Jen `893dd189...9ff5`; only Bedroom, Family and Jen are
  deployable plans.
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
- TV details is reconciled into one 12-file materialized tree. Every historical
  transformer input was verified from the Bedroom checkpoint chain, Family
  independently matched the final output hashes, and addon/family-manifest
  state is represented as typed assertions.
- News playback replays the current bounded-queue renderer from exact Family
  and Jen predecessors. Jen already has the current revision; the Family
  candidate advances from its older accepted revision. Shared manifest state
  is preserved and verified semantically rather than copied between hosts.
- Family media lifecycle replays four runtime files from its exact checkpoint.
  Intro Skipper is represented as a Jellyfin server assertion with pinned ZIP
  and DLL SHA-256 values; plugin databases and server state are not bundled.
- The Family equipment bridge is a preserve-and-verify external composition:
  exact HA/Agent/Remote recovery sources are bundled, device guard paths exclude
  external hosts, and seven HA/Agent/OPNsense/key assertions carry live state.
- Jen's account registry materializes nine immutable add-on/keymap files while
  explicitly excluding mutable profile, authority and credential-bearing state.
  The remaining Jen overlays must depend on that owner instead of rewriting it.
- Jen's Aster client now owns only its eight immutable voice/dialog add-on files.
  It depends on the account registry and excludes broker keys and mutable
  identity state, eliminating the old installer's cross-overlay rewrite path.
- Jen's News icon overlay replays its accepted digest base through the pinned
  four-pill renderer and carries the final XML, stable base/renderer and boot
  unit as one exact-hash composition.
- Jen's podcast-request overlay replays both accepted Books/Podcasts skin bases,
  carries the immutable add-on and boot reapply tree, and excludes private
  broker configuration and request receipts as mutable state.
- Jen's Guest catalogue overlay owns only the five immutable adapter files. It
  depends on the account registry and verifies the restricted Jellyfin client
  policy while excluding credentials, profiles and add-on state.
- Jen's Home/Cameras composition owns only its Home/Cameras XML, on-demand
  viewer, display marker and boot lifecycle. Its new composed reapply path no
  longer overwrites account or voice modules; HA mapping and private client
  files are typed external assertions.
- Jen's Movie/YouTube composition binds the accepted live Movie, dispatcher,
  trailer, YouTube navigation and graceful-stop outputs. Its composed boot path
  no longer rewrites account modules, private YouTube state is excluded, and
  shared family-manifest pins are typed assertions.
- Jen's low-spec composition materializes the 21 hostname-gated outputs not
  owned by later feature overlays and the exact Jellyfin policy code/units.
  The four superseded outputs are explicitly delegated to TV, Movie and News;
  client settings, credentials and Arc server HWA remain typed external state.
- Bedroom, Family and Jen have no incomplete overlay contracts and are the
  three deployable bundle-build plans. Guest remains a
  non-deployed candidate.
- Payload and dependency drift tests fail closed.
- The timestamped observation collector and fleet Doctor are complete. Doctor
  checks only deployed devices and reports missing, stale, future, malformed or
  composition-mismatched evidence as attention. Its first repository run
  correctly reports Bedroom, Family and Jen as unobserved; observations are
  runtime evidence and cannot alter desired state.
- No live appliance, wiki, network, Home Assistant or remote repository changed.

## Next

Run the bounded Jen migration/recovery rehearsal, collect its first fresh
observation and prove reboot/playback/rollback. Eligibility does not authorize
deployment; Bedroom, Family and Jen must still pass observation and recovery
rehearsal before promotion.
