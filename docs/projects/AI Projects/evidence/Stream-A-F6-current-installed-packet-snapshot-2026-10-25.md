# Stream A F6 current installed packet snapshot — 2026-10-25

Status: **READ-ONLY SNAPSHOT COMPLETE; REVIEW INPUT ONLY**

At 22:48 PDT, Stream A independently re-read the installed packet needed by a
replacement candidate-H/M3 activation card. No unit, lease, service, workload
or model was started.

## Host composition

The current composition root is
`/usr/local/libexec/local-ai-lease/stream-a-evaluation/`:

| Installed path | SHA-256 |
|---|---|
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | `3d6e976b5fcb33a5645ec35fd0fe337ebbb57600edbbd03fe074b165e440a4d7` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | `2d4ff31f75dc98af9f745ca7e24310ac3627b9b36e8a29bf9a50f8debb0911f0` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | `d3c8924e4e1cb5165d70ca36a4fc335b465445d1881390a8ba7c83ab44a508ed` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py` | `19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_admission.py` | `3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_effect_driver.py` | `06318de809a22321b254713a9af9b87aecfa150c1cfd298c164fcab16d961f0e` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_evidence_loader.py` | `836f627cd2702dffd59c77b77adab2aded01805ee43553a11471cfddfeb80a01` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_handlers.py` | `6977af891af538989de49c6cc67f13fe7d6953b68a9bd9d44bc9edadbbeed4a4` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_host_outcome.py` | `a9584bf01fea83129b8efb9a4c315ab66a37369ee386319f5632222618742225` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_live_plan.py` | `0f8d7e558bff48d6be9f86da62041ccaa20aa6b18780b738756d1118f0bf0ef2` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner.py` | `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner_heartbeat.py` | `4c45a07098eb8cca31bf95bb50b0824b65c6772e636627b23219761f359ed6cc` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_prepare_only_exercise.py` | `29429e7f5ff5252fed46b9cf27865d29ea1d891d14472739a056dc1ecc0eaa1e` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restore_observer.py` | `20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restored_verifier.py` | `a83de6bcdf0b275b9f238acda1a35e7518eae12f47eb220faf8f822d9a5e0d93` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_runtime.py` | `7cda2842afa25bfca9cb47e30f433474c440ccf18123c80e7c55b54c66eb7210` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_sequence.py` | `63eedd771d3cca25183e7f551b076c19d84e9c2855d9c7985e8cce445239aef1` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_watchdog.py` | `c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849` |

The trusted observer `/usr/local/libexec/local-ai-lease/trusted_observer.py` is
`6091b5572764abf3675d9140e760083a1482fee8abfef8fc763fb72853618f5f`.
The five wrappers remain:

| Wrapper | SHA-256 |
|---|---|
| `/usr/local/sbin/stream-a-evaluation-lease` | `15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af` |
| `/usr/local/sbin/stream-a-evaluation-owner` | `4d4e848eeafffdfa3aa9a0ba84097d94487318235442b1a4e4b8edc04a043014` |
| `/usr/local/sbin/stream-a-evaluation-owner-heartbeat` | `e0162f60983601192c5f0fdd6d8395604e6636c05c9653c643d3722872dce12a` |
| `/usr/local/sbin/stream-a-evaluation-watchdog` | `65012c196134242a76a2131fbc9d7f28b50bcfd9137a87cfda0a416345430c99` |
| `/usr/local/sbin/stream-a-evaluation-restore-observe` | `5cb6bec83864b5a8eeeb1b8c0624b93498fc04b2fcf36afb61e13caa0e64e8ab` |

## Units and guests

The five owner/watchdog units are:

| Unit | SHA-256 |
|---|---|
| `/etc/systemd/system/stream-a-evaluation-owner.service` | `640c753b5ba2a5b0555fce37b91dadd66c6e171ab40143fa6ba51309d97e2371` |
| `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.service` | `7bbb32a64a73b8797f34df934f9f06932c0706f93dc078b08bbc2c737d364f1e` |
| `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.timer` | `a5840b5b4a5bb56b0a05d6641fdaf1f16ca982c1c137bbb9e29f2d4b4b063192` |
| `/etc/systemd/system/stream-a-evaluation-watchdog.service` | `02ff7c4a909228023c1cce8704fd9d3e3395f5101add78a919481cbb4a39d932` |
| `/etc/systemd/system/stream-a-evaluation-watchdog.timer` | `7b2170f6f6d5e137fee14464b3081d229f37f36af1e1856cbc3de4ed3de79811` |

The owner-heartbeat service is the accepted owner-before-heartbeat correction
and supersedes the earlier card's `6c777750…2ad5` pin.

LXC104 and LXC110 both have `/usr/local/libexec/stream-a-evaluation-guest-outcome`
at
`027183c9f10923cc4aa3053934b5f090d8e01f86aa81c9730d93abc143e6dcb9`
and `/usr/local/libexec/stream_a_evaluation_outcome_verifier.py` at
`9408623489d52f7923c8dcca246159bb13a7926aa0a820c765fc8f3a339b58e1`.
Candidate-H's LXC104 launcher `/usr/local/libexec/aster-d4-candidate-h-launcher`
is
`71c07060a59a81923803fdd21cc14f218fc3c1c1f7f1797e1b1e75acdf4240eb`
and its unit `/etc/systemd/system/aster-d4-candidate-h.service` is
`76c0ba89b26124b1e0fb74e3ddc761a001d937195c4d14ce0c3b5ab0d6b62450`.
The LXC110 metadata-auth helper `/usr/local/libexec/aster-a1/llama_auth_probe.py`
is
`93e78f8a9c40bb9808ac71c5215404c8f10b3e5116383095d196281293682582`.

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
