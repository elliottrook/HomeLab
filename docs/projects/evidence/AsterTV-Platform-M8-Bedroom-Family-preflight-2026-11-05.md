# AsterTV Platform M8 Bedroom and Family preflight — 2026-11-05

## Outcome

Bedroom and Family are build-eligible for later ordered migration, but neither
appliance was changed. Read-only inspection found clean predecessor guards,
exact identities and small, declared payload deltas. Promotion remains gated on
owner physical acceptance of Jen and a separately authorized live milestone.

## Identity and predecessor state

| Target | Identity | Runtime | Current guard | Audio contract observed |
|---|---|---|---|---|
| Bedroom | `AsterTV-Bedroom`, `192.168.1.140` | LibreELEC `nightly-20261021-440640e`; Kodi active | enabled and clean, 535 files | two-channel PCM base; passthrough on; AC3/EAC3 on; DTS/TrueHD/DTS-HD off |
| Family | `AsterTV-Family`, `192.168.1.157` | LibreELEC `nightly-20261021-440640e`; Kodi active | enabled and clean, 533 files | two-channel PCM base; passthrough on; AC3/EAC3/TrueHD on; DTS/DTS-HD off |

Family's live ED25519 fingerprint
`SHA256:qup6j5SaoLYSgeUyrMbXMD2+lpd+DGupbgO6DkHxhm8` exactly matches the
repository-pinned production identity. The key was absent, not mismatched, in
the Mac's persistent trust file; discovery used a non-persistent trust override
after fingerprint comparison and did not alter the trust store.

Bedroom's desired profile was stale: it described passthrough as disabled even
though the owner had accepted and retained AC3/EAC3 passthrough. The fleet
profile, declarative payload, wiki candidate and regression assertions now
describe the existing live behavior. No Bedroom setting was changed and no
Family audio capability was generalized into Bedroom.

## Reproducible candidate evidence

The full fleet compiles after that source reconciliation. Verified bundle-build
preflight against the immutable v2.0.7 base produced:

| Target | Composition | Bundle SHA-256 | Build gate |
|---|---|---|---|
| Bedroom | `84b045b84a7d…` | `2668ae56c3dd5d0cf14a666121018002d3338d4834b2f9694985f9f8aa2776aa` | eligible |
| Family | `c2a578002f94…` | `2eeb34684fa4346fd094039c7ccc49aa405d06eb91dc265c2118e3b599d8d288` | eligible |

Generated bundle bytes remain disposable build outputs and are not committed.
Guest remains non-deployable; Jen retains its separate media-only 1080p/stereo
ceiling and native-resolution GUI.

## Read-only installed delta

The Bedroom contract has 25 installed payloads: 24 match and one differs. The
only replacement is `/storage/.aster-release/release_guard.py`.

The Family contract has 35 installed payloads: 29 match and six differ. The
replacements are limited to the release guard and unit, Family manifest, and
the three declared News playback files. There are no missing payloads on either
appliance and no unknown path was introduced.

## Required migration order and gates

1. Obtain owner physical acceptance of Jen's compiled composition.
2. Build and re-hash the accepted Bedroom artifact; reconfirm identity, idle
   playback, Wi-Fi, audio settings, checkpoint and exact delta.
3. Migrate Bedroom first. Prove Wi-Fi reconnect, stereo PCM, AC3/EAC3
   passthrough, remote/navigation, reboot, Doctor and exact rollback/reinstall.
4. Only after Bedroom acceptance, rebuild and migrate Family. Preserve measured
   Dolby/HDR, PulseAudio mask, News/Music lifecycle, equipment bridge and room
   controls; repeat reboot, Doctor and rollback/reinstall.
5. Recompile all active compositions and leave Guest non-deployed.

Stop on active playback, identity uncertainty, a new path/delta, unavailable
checkpoint, audio/HDR/Wi-Fi regression, dependency loss, failed rollback or
any change outside the named target.

## Validation

- HomeLab Wiki department tests: 3/3 passed.
- AsterTV design authority: 12/12 tests and 28/28 generated outputs passed.
- Onboarding planner: 7/7 tests passed.
- Fleet/release: 47/47 passed, including focused Bedroom and Family audio
  subset gates.
- Shared v3 regression suite: 37/37 passed.

No appliance, network, Home Assistant service, firewall, NetBox record,
credential, wiki deployment or mirror changed during this preflight.
