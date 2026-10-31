# October31 nightly reconciliation — source-update preflight

Local-only continuation of the nightly loop. No push, deployment, timer change,
lease claim, guest checkpoint or model request. The supplied heartbeat arrived
outside the booked overnight window; it does not launch a duplicate owner.

## Reconciled evidence and research ranking

Shared ownership metadata currently shows no lease/drain/operation markers or
common directory-flock holders. Existing immutable receipts remain unchanged:

| Proxmox path under `/var/lib/local-ai-lab/` | SHA-256 |
|---|---|
| `exclusive-integrity/b60-exclusive-20261031/terminal.json` | `e057efd5949b94dd42e92a25b8d3fb48fd588df8bf38d2e5e3549b35719f6b8c` |
| `exclusive-sessions/b60-exclusive-20261031/admission.json` | `4e81d8f9d8bb9d13772b2312b877722ee1960ef8f1e7df946228f38e7900bf40` |
| `reservations/records/b60-exclusive-20261101.json` | `55ed0e33edf8c1db637cf6cc357d2250af2599aabb4f3b4fb4b0d898a3116d4f` |

October31 session checkpoint remains absent; next activation remains absent.
Do not turn a completed archive scan, admission receipt or launcher exit0 into
restoration qualification. The [cross-host clock hazard](backup-clock-hazard-20261101.md)
remains the operational timing gate, not a reason to extend restoration.

Re-read the expanded programme from the full checkout (SHA-256
`27f416c32d2cc1b895effc438c80a55e6616282c9597434a0fe8f747e078acaf`)
and the October26/current ranked research record. Rank1 remains ordinary
Qwen3.6-35B-A3B Q4_K_M on accepted b11429/SYCL, reasoning on, speculation off,
two sequential synthetic correctness requests **after** fit/recovery gates.
No acquisition, mount, runtime upgrade or model call occurred. Retain newer
SYCL memory/corruption hazards as version-specific leads, not accepted fixes.
The24-case paired screen is not the two independent sessions/100 observations
per acceptance class needed for final useful-answer p50/p95 claims. No fresh
baseline, harder-task superiority or27B+ milestone is claimed.

## Concrete installer defect and source-only correction

The no-overwrite dormant installer previously compared each existing source
while iterating installation. If an earlier source was absent and a later
existing source differed, it could add the earlier file before refusing. The
late mismatch remained fail-closed for activation, but it was not an all-write
preflight. Do not describe this as an observed production mutation: it was
identified and reproduced in disposable local fixtures.

Implementation `a30322cb2a8da5bc0cf21ad4ea5400ee85dc4dd3` now inspects the
whole existing destination under the same exclusion before creating a package
directory or writing source. It rejects unsafe directory custody, target
symlinks, extra files and any changed existing bytes first. Absent or partially
present identical packages remain resumable. Existing per-file checks remain
as a second barrier. This does **not** remove the no-overwrite rule or turn the
installer into a source upgrader.

Five new synthetic tests prove late-sorted drift prevents both directory and
put operations; extra/symlink targets refuse; absent targets stay absent;
partial identical targets remain untouched; unsafe custody refuses. Ten
installer tests pass, plus136 Lab Hours tests and115 B60 tests against the
exact independently replayed tree `5bdc000aa1a02b938804a0fec4d66c3bd34f59dc`.
Implementation and replay trees are equal. Custody fixtures substitute UID
metadata on the Mac; these are not live Linux custody or restoration proof.

Source-only installer SHA-256:
`65b049f0a059602545ed6cd30041da7daed3fc3b24075a0eb0600f0eea6b3968`.
Portable patch:
`scripts/b60-inference/dormant-preflight-20261031/0001-Preflight-every-existing-dormant-source-before-any-p.patch`,
SHA-256 `fb771775b6233da37d8e5f8cc2f8416b0874fd100a6cf8a395a096f7011506ba`.
Apply after the existing diagnostic/clock regression patches through
`546d85b2c`. No patch was copied to any host.

## Exact diagnostic transition packet, not an executable upgrade

Built a fresh local30-file candidate closure at
`/private/tmp/b60-exclusive-diagnostics-20261031-nightly-v1` using the provided
builder; manifest reports `installed=false, armed=false`. Descriptor SHA-256
`5e53c5242d027d2fb854f27d3a007242e34abcd6d0b5a4bf65385b73303251a0`;
canonical sorted compact pin-map SHA-256
`c9fbbd2039b1dabe0771a2b27128147df1be860ce88a2bf4317b4c504f17d739`.
Compared every dependency against retained old v4 closure, descriptor
`ce2ed7f7165160277eb627e496077adfd8c8fe6d476b62a2d888429f76d10ab4`,
pin-map `f5085fbb7b7e8e456be6ac6157867a1af8e808a2e139fb64c03caeb991d25e85`.
Exactly two host modules differ; all28 others, including all guest helpers,
are byte-identical:

| Module | Installed old SHA-256 | Candidate SHA-256 |
|---|---|---|
| `lab_hours_exclusive_admission.py` | `69338eaea4a63575caca059a23697e440e60a89cda06fb9f95d78d19848b6886` | `442159a032700694c7d4e7f60bd7050f70d83cf0764ac3646724f6cb2c88b6ec` |
| `lab_hours_exclusive_cli.py` | `9f48ed0b828d6a1001f0b9122b9fcc5b192afcf9e70353699a617c8f01f30469` | `64f7e5458ccc93b2754e3196ddcab4bda4a094c759c7a0f2a8174d173a627d02` |

The newly corrected installer is outside that runtime closure. It still must
refuse this transition against old code. No executable updater is delivered
by a bundle or transition table.

Next source-update work: implement/test an exact two-module reversible
transaction, independently prove no active owner/guardian/recovery or armed
future old-profile consumer before writes, checkpoint old non-secret source
under protected custody, verify full old/new dependency sets, retain an
immutable transition journal and validate imports before enabling a fresh
profile. Rollback may restore only recognized transaction-owned old/new bytes;
unknown drift must retain evidence and refuse, never overwrite peer work.
Interrupted transitions must never leave an armed owner selecting mixed code.
Keep historical profiles/receipts unchanged. The source-update transaction and
clock correction remain unimplemented/undeployed gates, not approval waits.

## Authoritative receipts and lifecycle limits

Fetched/read the four authoritative refs. Exact unchanged peer receipts are
linked from [October31 reconciliation](qualification-no-go-20261031.md).
Received B60 now `498e5f4647f117e104a979e128a68a6bd00229d7`, path
`docs/projects/B60-Inference-Engineering/backup-clock-hazard-20261101.md`,
SHA-256 `f63b8c443f94c7adf20db24bb50aa07d57e14c0d3bfad50ba3bf75c5da43f7d1`.
Adaptive remains `d88f8239b6771836c3e56c59229db81a8c18ddd6`; registry
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`; booking owner
`5a9c3471398cfeecc0c6db35bfb264f87d8318f9`. No peer reading inferred.
Read-only GitHub protection ref matches the published B60 received commit.

Additional lifecycle/release records read at registry commit above:

- `docs/projects/Production-Service-Placement-and-Release-Registry.md`,
  SHA-256 `b7482ba17357f0dbdbab29fa5a7b7fe3437e970303627f959098f33eca2cfae2`.
- `docs/service-release-registry.md`,
  SHA-256 `d93de63ad79e3980568335b485b0713041f43bdf7e36f3f46f584de9c5b060d8`.

Their referenced `docs/Environment-and-Release-Lifecycle.md` is absent from
that fetched ref and the existing full checkout; no contents or new lifecycle
authority were invented. The available registry still explicitly distinguishes
V1 release, upstream build/model/configuration, transitional VLAN70 placement
and separately gated promotion. This record changes none of them. Missing
reference is a documentation gap, not authority to stop all safe preparation.

Local-only commit per nightly instructions. No push or new background task;
the existing programme remains active. Next check-in resumes from the explicit
source-update and clock gates, never replays the expired October31 booking.
