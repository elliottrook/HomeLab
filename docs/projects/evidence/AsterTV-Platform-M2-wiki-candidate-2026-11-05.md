# AsterTV platform M2 existing-wiki candidate

> Status: local candidate complete; human acceptance, Forgejo synchronization,
> LXC 113 publication and mirror derivation are pending
>
> Captured: 2026-11-05
>
> Scope: additive authored pages, pinned intake candidates and local validation;
> no live wiki, collector, mirror, appliance, credential or remote changed

## Existing platform preserved

The candidate extends the existing private `homelab-wiki` MkDocs repository and
its Human Wiki Contract. It does not create a parallel wiki, alter the LXC 113
collector, bypass provenance/quarantine, overwrite generated paths or edit the
derived Aster mirror. The authored candidate is local wiki commit `1fdcf6a` and
has not been pushed or published.

## Candidate content

- 25 AsterTV pages under `docs/astertv/` plus an additive MkDocs navigation
  branch and Home link.
- Start Here authority/ownership workflow, fleet/release matrix, four device
  pages, hardware/peripheral profiles, build/release and onboarding/retirement.
- Curricula for Kodi/LibreELEC, Jellyfin/playback, ARR/requests,
  books/listening, YouTube, Home Assistant, OPNsense/network, identities,
  Aster services, backup/recovery and monitoring/Doctor.
- Incident/problem handling, role competency matrix and a plan-only synthetic
  Bedroom focus-regression exercise.
- Explicit M3 design-system placeholder that preserves accepted icon/focus
  rules without presenting the future pattern library as accepted.

Every page declares owner, authority, applicability, review date, sources and
recovery. Device pages preserve Family Dolby/HDR/equipment control, Bedroom
stereo/Wi-Fi, Jen's device-only 1080p-media/stereo limit and Guest non-deployment.

## Pinned intake candidates

`services/aster-wiki/source-batches/milestone-astertv-platform-m2.json` uses the
existing manifest/collector contract for two missing upstream references:

| Source | Pinned commit | Boundary | Policy |
|---|---|---|---|
| Kodi 22.0 RC1 Piers | `28ea2eac1eb7af8fdcbd2672d933ce87f594be79` | README and license | allow derived |
| LibreELEC documentation | `b6dbb88400ed805ea9a81dafe0cf110db55f7f4a` | bounded install/security/HDR/EDID/audio/startup/log/update pages | human only |

Both manifests passed strict schema validation and a real bounded `fetch_git`
plus collector validation. Fetched commits matched exactly; normalized input
sizes were 8,467 and 62,346 bytes. No source was enrolled or accepted live.

## Validation

| Gate | Result |
|---|---|
| Department completeness | 25/25 authored pages present in MkDocs navigation |
| Metadata | required owner/authority/applies/review/sources/recovery on every page |
| Internal links | all repository-local links resolve and remain inside the repository |
| Freshness | current date passes; a 2027-02-04 synthetic date fails closed on expired review |
| Adversarial link | injected missing target is rejected |
| Secret pattern | zero secret-bearing assignment findings |
| Unit tests | 3/3 pass |
| Source manifests | 2/2 schema, pinned fetch, hash/ref and collector validation pass |
| Diff hygiene | `git diff --check` clean before the wiki commit |

MkDocs is not installed in this local macOS environment, so rendered-site
generation remains a publication preflight on the established LXC 113/tooling
path. This is not bypassed: human visual/content acceptance and the existing
site build must pass before deployment or mirror derivation.

## Gate assessment and next action

Start Here alone routes an engineer through target identification, symptom
classification, authority/owner resolution, deterministic composition,
checkpoint/idle planning, validation, rollback and stop conditions. The linked
synthetic exercise tests that the engineer rejects profile deletion and an
unrelated Wi-Fi edit, preserves all four device contracts and adds a regression
fixture without touching a live system.

Next, Jason reviews the candidate content. After explicit remote-write approval,
push the HomeLab and wiki commits to their respective Forgejo origins, verify the
automatic GitHub protection mirror where configured, then use the established
LXC 113 publication/intake flow. Only after the human pages are accepted may the
derived Aster mirror be rebuilt.
