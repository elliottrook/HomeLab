# Local Proxmox whole-job proof repair — disabled-install card

Status: disabled-stage repair installed and verified; live pilot remains
unauthorized.
This card fixes the stale Proxmox task-list admission path used by the
disabled full-inference pilot. It does not authorize a pilot, guardian
prearming, service changes, timer changes, or a remote push.

## Problem and bounded design

The installed `dafc0332` source asks `pvesh` for the current node task list.
That list is short-lived and had already aged out the 00:30 backup, producing a
false NO-GO even though the durable backup task record still existed. The
repair queries only the bounded `pvescheduler` journal window for the cycle and
requires exactly two JSON records, in order:

1. the root-owned `vzdump` start message with the actual Proxmox UPID format;
2. the exact `INFO: Backup job finished successfully` message.

It also retains the fixed backup-job configuration, Vancouver 00:30–00:35
start window, and artifact custody ordering:
`start <= latest artifact ctime <= finish <= now`. Missing, extra, malformed,
error, task-list-only, or out-of-window evidence fails closed.

## Exact source delta

Target source tip: `dafc0332`. Replace only these four source/test files when a
separate install approval is granted:

| File | Target SHA-256 | Repair SHA-256 |
|---|---|---|
| `scripts/local-ai/full_inference_lab_sources.py` | `1f53e61b6909c26b6658d17396eff9babb4f2253b470fe33d8b188bfc9980c39` | `233459b80bf927a53b32d11563bf2e0b264ab25ad55091293e6f40995747e054` |
| `scripts/local-ai/full_inference_lab_validator.py` | `5cf1562a98c7a01528c5e3f2e2d80c69c5805f0e9dc4fceec1916d15d0d686f4` | `88ab982853c4ad04f9d9d5892e42ae2d22c3741ed7ac1ed927267f0356d575ad` |
| `scripts/local-ai/test_full_inference_lab_sources.py` | `eab6fb2fc1bc7aa0dd14ee001aee7a58bafb73faf5b3c0f0adb52b31e5be8650` | `9a1c3abf5179c9f2933fce6936c0e8c23c839275ffb7e4d718a81359268257ae` |
| `scripts/local-ai/test_full_inference_lab_validator.py` | `b3806c9e769dbcf77efe23d616147365961087c91e7cd6413e3e7cb8c6341f91` | `75dbe8afe4b925844702a33339356414ceb955dfa4cb3603da97a43fd75ef4d5` |

The exact journal command is generated from a validated `YYYY_MM_DD` cycle;
the source does not accept an arbitrary shell string. The repair is installed
only in the existing inactive pilot directory; no unit or timer was enabled.

## Verification completed

The focused source and validator tests pass. The complete local-AI suite
passes: 297 tests, 4 expected skips. Verification includes the real trailing
colon in the observed Proxmox UPID, successful artifact custody, missing
whole-job rejection, local-only no-TrueNAS behavior, and validator release.

Target-Linux installation verification also passed: 65 tests; exact repair
hashes; exact rollback checkpoint at
`/root/aster-pilot-backup-source-rollback-c66b9ae8`; and the live
`LocalProxmoxFullDrainSourceProducer` returned `local_backup_proof=True` for
the current 2026-10-18 cycle. The bounded journal contained the expected
00:30 start and 00:50:40 completion evidence. The postcheck found no pilot
scope, guardian unit, 11436 listener, pilot process, model call, service stop,
or timer change.

## Install and rollback gate

Rollback restores only the four target hashes from `dafc0332` using the
checkpoint above; do not alter the already installed runtime/guardian
upgrade. The installed repair makes the local backup source gate pass, but it
does not authorize a pilot, guardian prearm, service drain, or remote push.
