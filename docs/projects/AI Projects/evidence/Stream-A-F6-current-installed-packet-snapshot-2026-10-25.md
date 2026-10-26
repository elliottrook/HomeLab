# Stream A F6 current installed packet snapshot — 2026-10-25

Status: **READ-ONLY SNAPSHOT COMPLETE; REVIEW INPUT ONLY**

At 22:48 PDT, Stream A independently re-read the installed packet needed by a
replacement candidate-H/M3 activation card. No unit, lease, service, workload
or model was started.

## Host composition

The current composition root is
`/usr/local/libexec/local-ai-lease/stream-a-evaluation/`:

| File | SHA-256 |
|---|---|
| `evaluation_lease.py` | `3d6e976b5fcb33a5645ec35fd0fe337ebbb57600edbbd03fe074b165e440a4d7` |
| `evaluation_lease_adapter.py` | `2d4ff31f75dc98af9f745ca7e24310ac3627b9b36e8a29bf9a50f8debb0911f0` |
| `evaluation_lease_entrypoint.py` | `d3c8924e4e1cb5165d70ca36a4fc335b465445d1881390a8ba7c83ab44a508ed` |
| `evaluation_lease_watchdog.py` | `19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53` |
| `host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `stream_a_evaluation_admission.py` | `3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686` |
| `stream_a_evaluation_effect_driver.py` | `06318de809a22321b254713a9af9b87aecfa150c1cfd298c164fcab16d961f0e` |
| `stream_a_evaluation_evidence_loader.py` | `836f627cd2702dffd59c77b77adab2aded01805ee43553a11471cfddfeb80a01` |
| `stream_a_evaluation_handlers.py` | `6977af891af538989de49c6cc67f13fe7d6953b68a9bd9d44bc9edadbbeed4a4` |
| `stream_a_evaluation_host_outcome.py` | `a9584bf01fea83129b8efb9a4c315ab66a37369ee386319f5632222618742225` |
| `stream_a_evaluation_live_plan.py` | `0f8d7e558bff48d6be9f86da62041ccaa20aa6b18780b738756d1118f0bf0ef2` |
| `stream_a_evaluation_owner.py` | `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1` |
| `stream_a_evaluation_owner_heartbeat.py` | `4c45a07098eb8cca31bf95bb50b0824b65c6772e636627b23219761f359ed6cc` |
| `stream_a_evaluation_prepare_only_exercise.py` | `29429e7f5ff5252fed46b9cf27865d29ea1d891d14472739a056dc1ecc0eaa1e` |
| `stream_a_evaluation_restore_observer.py` | `20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2` |
| `stream_a_evaluation_restored_verifier.py` | `a83de6bcdf0b275b9f238acda1a35e7518eae12f47eb220faf8f822d9a5e0d93` |
| `stream_a_evaluation_runtime.py` | `7cda2842afa25bfca9cb47e30f433474c440ccf18123c80e7c55b54c66eb7210` |
| `stream_a_evaluation_sequence.py` | `63eedd771d3cca25183e7f551b076c19d84e9c2855d9c7985e8cce445239aef1` |
| `stream_a_evaluation_watchdog.py` | `c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849` |

The trusted observer is `6091b557…18f5f`. The five wrappers remain
`15f3de1e…71af`, `4d4e848e…3014`, `e0162f60…12a`, `65012c19…c99` and
`5cb6bec8…e8ab` for lease, owner, heartbeat, watchdog and restore observation
respectively.

## Units and guests

The five owner/watchdog unit hashes are `640c753b…2371`,
`7bbb32a6…f1e`, `a5840b5b…3192`, `02ff7c4a…d932` and
`7b2170f6…9811`. The second value is the accepted owner-before-heartbeat
correction and supersedes the earlier card's `6c777750…2ad5` pin.

LXC104 and LXC110 both have guest outcome wrapper `027183c9…dcb9` and
verifier `94086234…58e1`. Candidate-H's LXC104 launcher is
`71c07060…0eb` and its unit is `76c0ba89…2450`. The staged M3 runner is
`a8cca4da…5a0f`; the LXC110 metadata-auth helper is `93e78f8a…2582`.

The M3 identity above is historical. The later
[current M3 coordination receipt](Stream-A-F6-current-M3-packet-coordination-2026-10-25.md)
supersedes it with the installed final runner, scorer, journal and packet
manifest identities. The host/V3 identities in this snapshot remain the
current review input.

## Review consequence

The replacement activation/recovery card must pin this complete installed
boundary, not the pre-V3 subset. It must also keep candidate-H then M3 as the
only admitted sequence. The fixed Doctor usefulness packet is a separate
third-workload proposal and must not be silently appended.

This snapshot exposes one useful review rule: the M3 stage-manifest identity
is a packet digest, not an installed file called `stage-manifest.json`; that
path does not exist in the staged directory. A future card must bind the
accepted packet digest without inventing an installed path.

Fresh F2–F5 evidence, independent recovery readiness and explicit live effect
approval remain mandatory. This snapshot grants none of them.
