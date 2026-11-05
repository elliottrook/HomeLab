# November5 restore-only qualification — operationally armed

Jason explicitly requested completing the guarded migration and arming now.
This operational continuation completed both; it is not a preparation-only
heartbeat or a claim that the future qualification passed.

## Independently observed arming

At Proxmox epoch1793838226 both date-specific timers were enabled, active /
waiting, with empty `LastTriggerUSec`. Their services were inactive/dead,
MainPID0 and empty start timestamps:

- `b60-exclusive-integrity-20261105.timer`: November5 **01:15 Vancouver UTC−07**.
- `b60-exclusive-qualification-20261105.timer`: November5 **03:10 Vancouver UTC−07**.

The host labels this fixed-offset Vancouver clock MST. TrueNAS independently
reports `Etc/GMT+7` /−0700. Its existing enabled tasks remain1→01:00,
3→02:00 and2→03:00. No clock, pull schedule or backup execution was changed.
The runtime must still prove the actual same-night backup/mirror chain.

Booking `b60-exclusive-20261105`, reserved/exclusive-stack, b60-stream-a,
start1793873400/end1793876100 (03:10–03:55), retains SHA-256
`1835efd57a32dc94312c9fc20de023d3990cefe5a990ff06d6d4ac18d63d6720`.
No duplicate reservation was created. Profile is qualification-only, experiment
null,300-second trial, all13 consumer units and five guest plans. Restore by
03:55, recovery buffer through04:10, protected04:15 boundary unchanged.

Actual protected receipt on Proxmox:
`/var/lib/local-ai-lab/arming-receipts/b60-exclusive-20261105.json`, SHA-256
`4cf3745bda67b923594044c1243db6d6135c73f2113e0af0844b1016fba2ffa4`.
It records timer/service states and all installed source/guest-plan checks.
Profile path `/var/lib/local-ai-lab/exclusive-activations/b60-exclusive-20261105.json`,
SHA-256 `d1a56414b570bcb89ed6df979e257208cab609e82e658aefd0ab8d6278d9dd15`.
Independent verification matched all30 deployed source pins and all five
plan/helper identities. No previous run or model experiment is scheduled.

## Guarded source migration completed

Fresh minimal metadata found no owner/drain/operation markers or matching
shared-lock holder; the established helper reported ready. Complete installed
source and retained old bundle matched c9, root-owned0600/one-link,30 files.
The exact claim-window packet was staged at
`/root/b60-claim-operational-20261104-v1`, archive SHA-256
`5b6e612a865f1ea4c1910a14c330a5aee9797abb1d02adda774d1fafd25f233e`.
Its30-file candidate and17-file tooling closures matched recorded descriptors.
Ten target-Linux real disposable file/process-loss tests passed.

The first updater invocation refused `PROFILE_PARENT_CUSTODY` before an attempt
or installed-source write: tar extraction had retained the local user's IDs.
Corrected only the new payload's ownership/modes to root-private and reran the
guarded adapter. Exact c9→e16 migration returned installed-not-activated;
all30 imports/pins passed. Protected receipts under
`/var/lib/local-ai-lab/source-updates/claim-window-20261102-v1/`:

- `files/manifest.json`: `12bd192606085099f62b363f3138c81a2cfefa7d0e490c09ab821c74227ced3b`.
- `journal/update.json`: `215b74b96b11f64a0d4d784545ce9bbc1f8b5dc2fc22143212f739f1653af192`, phase installed.

## Observed EPUB resource configuration is now included in restoration

Initial metadata-profile preparation refused before arming. Fixed-field
diagnosis showed104/110/114/115 prepared, while116 returned
`TARGET_OUTSIDE_DECLARED_SCOPE`. Unit metadata identified two legitimate
runtime resource-limit drop-ins:

- `/run/systemd/system.control/epub-narration-worker.service.d/50-CPUQuota.conf`
- `/run/systemd/system.control/epub-narration-worker.service.d/50-MemoryMax.conf`

Added only those exact files to the guest checkpoint allowlist, used by both
metadata planning and capture/restore. Arbitrary runtime files, other units'
resource paths and traversal remain rejected. No resource value or unit was
changed. Checkpoint restoration writes its temporary file beside the target,
so `/run` and persistent backup storage need not share a filesystem.

Source commit `4197bdbf22ae31813a04342fe09ae754475f7444` in
`/private/tmp/b60-resource-checkpoint-20261104` contains the narrow extension,
exact e16→resource source policy, guest source updater and tests. Portable patch:
`scripts/b60-inference/entry-resource-checkpoint-20261104/0001-Checkpoint-exact-EPUB-runtime-resource-files.patch`,
SHA-256 `0ea0fdec55106515aa92910d5e0d2fb13c55569e0ac15991b3883eeb59936a48`.
183 controller tests and115 B60 tests pass against this explicit source root.
Nineteen target-Linux disposable source/rollback tests passed, including failed
imports, corrupted/foreign source and actual child loss for host replacements.
These tests are not live stack restoration qualification.

Exact resource candidate descriptor
`d58e4c9e5f04e68319696a9eb5a27dc8212327c31ec5c7ff083337708afb4f18`,
final30-file pin-map
`20e2ce272634d13c7e40a0c625cd0c48a7c4e20716588d2bc950abe86a6f9b71`.
Final helper SHA-256
`76e8f228fcbcd302a67dbbfd8538a2f1e0dd2e39449b0e4745152c32aef9d76b`;
all29 other runtime files equal the claim-window candidate. Resource packet
`/root/b60-resource-operational-20261104-v1/packet.tar`, SHA-256
`315aa9e22520e6260e90e9a9f34a836c4aa674982483c6ec8b578ab0631eebc9`.
Its18-module tooling descriptor is
`6295914c1479e8b239191a0a481e1e36da625d460666f54b21ca6c1f929ac56c`.

Host helper migration ran through the shared-lock/pin/checkpoint/import guard.
Receipts under `/var/lib/local-ai-lab/source-updates/entry-resource-files-20261104-v1/`:
`files/manifest.json` SHA-256
`182f7ce3d5d2db9fefc331be8d3ee96e3e74bc19bb717dbabff44e5a2876d05a`;
`journal/update.json` SHA-256
`769d8a2d64f8caef5f3388915b9705f2037a451321cde5d5b4fa46483c73a585`.
Five guest-local helpers were migrated under one shared exclusion, with exact
old/new source comparison, retained source checkpoints and import rollback.
Each guest's checkpoint at
`/var/lib/local-ai-lab-entry/source-updates/entry-resource-files-20261104-v1/files`
has manifest digest
`af66a864ad7c7b02f0e431d9d5643e5eb7f80f1b02b5cdfeff058a4f851bac83`.
The identical digest reflects identical source/path/mode metadata, not copied
guest application configuration. Source and recovery bytes remain local.

Reran the dormant installer successfully: five metadata plans, no AI-stack
effects, no secret-bearing configuration copies. Then ran the reviewed dated
scheduler, whose source remains
`1a62e2da5217463b2f8dbce6362b8a8956ff1f18685f298898b69c869bcb0a64`.
Integrity producer remains
`af8e054b2032c80f3d27f95bee0e603ef34aefa9cb05ce2f0c60c4460fd85c01`.

## Postcheck and next action

Agent104, accepted inference110 and Speech116 services are active. News ingest
timer is active/waiting and digest timer active/running at postcheck1793838251.
Those are unit-state observations, not model/speech/application test calls.
Shared lease is ready. No current stack transaction, model/GPU call, mount,
service stop, package/driver/boot/credential change or model promotion occurred.
No old coordinator or expired booking was invoked. Existing peer work preserved.

The Proxmox owner/guardian now own the future booked qualification independently
of chat/Mini continuity. Next reconcile actual November5 integrity/admission /
session/terminal receipts. Fresh backup, consumer, capture, timing and recovery
gates may still refuse; arming is not success. Do not start a duplicate run.
Normal recovery, independent owner-loss and candidate/resource proof remain
before35B screening; full-Aster capability/p50/p95 qualification is still open.
No renewed model approval or further user action is needed for this arming.
