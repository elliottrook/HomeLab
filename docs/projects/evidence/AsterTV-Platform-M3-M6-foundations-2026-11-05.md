# AsterTV Platform M3–M6 foundations — 2026-11-05

> Status: local foundations complete; M3 owner visual acceptance and M4 live
> integration/recovery gates remain open.

## M3 design authority

`services/kodi/astertv-design/` now owns versioned tokens, asset/component/page/
focus/fixture schemas, a catalogue, focus contracts, deterministic generator,
runtime asset index and synthetic pattern library.

- 28 runtime assets are indexed by SHA-256.
- 15 accepted-v2 or v3-candidate page implementations are mapped.
- 24 synthetic fixture families have 1920x1080 SVG renders.
- 12/12 design tests pass, including deterministic generation, closed declared
  focus graphs, complete page-family coverage, fixed geometry and privacy.
- Read-only inspection of the private Forgejo release attachment verified
  archive SHA-256
  `2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc`.
  The semantic plain compass resolves to `SVG/15-aster-compass.svg` and exact
  32/64/128 PNG and WebP export hashes. Its allowed contexts exclude the
  limestone-only side rail and launcher.

The generated library is candidate review evidence. Tests do not substitute
for Jason's visual acceptance.

## M4 release/guard foundation

`services/kodi/astertv-fleet/build_release_plans.py` deterministically emits a
plan, CycloneDX SBOM and desired-state guard contract for Family, Bedroom, Jen
and the Guest candidate. Compatibility/deprecation policy and per-hardware
performance budgets preserve Jen's 1080p-media/stereo limit as Jen-only while
allowing a native-resolution GUI.

The immutable local v2.0.7 archive now matches its recorded SHA-256 for every
composition. All plans still deliberately report `deployable: false` and the
blocker `composition-bundle-not-built`; Guest also reports
`candidate-not-deployable`. `composition_guard.py` classifies clean state,
registered extras, missing/unknown resources, dependency loss, composition
drift and identity mismatch. The combined fleet/release suite passes 17/17.

The atomic transaction fixture injects an interruption after the predecessor
move, proves automatic predecessor restoration, then proves normal promotion
and isolated rollback to the old bytes.

This is not yet a deployable global/profile/overlay bundle and is not wired into
the appliance guard or HomeLab Doctor. Each overlay must first declare exact
payload paths and hashes; metadata-only packaging is intentionally rejected.

## M5 onboarding foundation

The plan-only onboarding helper produces NetBox, deny-by-default network, Home
Assistant, acceptance, recovery and operator plans. It rejects active or
unknown devices, literal addresses without NetBox authority, secret/arbitrary
execution fields and undeclared control capability. Seven of seven tests pass.

The synthetic Guest plan remains correctly blocked on hardware measurements,
NetBox VLAN/address allocation and physical display/power chain registration.
No address, hardware, identity or permission was invented.

## M6 skills

Created and installed:

- `astertv-fleet-engineer`
- `astertv-design-engineer`

Both are source-hash manifested, refuse overwrite during deterministic install,
and pass the official `skill-creator` validator. The active installations under
the user's Codex skill directory match the committed source hashes.

Independent forward tests used a Guest onboarding request and a 12-season TV
design request. Fleet behavior passed without effects or invented facts. Design
behavior rejected stone-backed top-rail icons, used an eight-row scrolling
season viewport and stopped on the initial semantic asset ambiguity. After the
exact Forgejo asset mapping was added, the focused re-test passed with no
residual selection ambiguity.

## Effect boundary

No AsterTV appliance, Kodi installation, Home Assistant instance, OPNsense,
NetBox, LXC 113 wiki, Aster mirror, credential or remote repository changed.
Only the two explicitly requested Codex skill packages were installed locally;
their installer and exact source manifest are retained in Git.
