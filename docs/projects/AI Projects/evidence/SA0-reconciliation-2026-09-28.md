# SA0 reconciliation — initial manifest and release decision

Date: 2026-09-28
Status: **active; initial inventory complete, reconciliation open**
Scope: read-only source/runtime inspection after the approved Operational Sysadmin
Capability workstream was published. No guest, model, credential, service, firewall
or runtime configuration was changed.

## Publication and source history

Forgejo `main` and its configured GitHub mirror both resolve to
`007ef8282ced0e5c17669c8f1b93ed68ecad3a0e`. It merges the prior Forgejo main at
`ca22e788e78b6ec56b1a800da543f08bf30abcd2` and the adaptive-workstream history
containing `6dc2f435c70e22ff87b1dcce088ebe2c4b16e5c0`.

SA0 then established that the local production-history tip `d2f771d` is **not** an
ancestor of `007ef82`. It contains the September 27 Companion/passkey and AI-PAM
interface work and the September 28 archive repair. The running gateway's UI/passkey
differences correspond to commits on that omitted history. `007ef82` is therefore a
published integration checkpoint, not the completed reconciliation release. The
next SA0 action is to merge `d2f771d` into the published branch, resolve conflicts
while retaining all three histories, validate the resulting source manifest, then
publish that merge. The earlier statement that those production repairs had already
been preserved by `007ef82` was incorrect and is superseded by this finding.

The first merge conflicts were limited to the changelog and programme records. Both
included histories are retained; the old 2026-09-26 integrated checkpoint is
explicitly historical, while the programme's 2026-09-28 controlling resume
instruction governs next work.

## Running runtime manifest

| Component | Observed state | Reconciliation result |
|---|---|---|
| Aster gateway | LXC 104; `aster-agent` active; uvicorn bound to `192.168.70.10:9120`; running file SHA-256 `f7b5c82b8a401162e5151a2c8289b061e3d4a8bb162fa9598997ed67081e99a1` | Diff corresponds to omitted local production history; merge that history before any gateway deployment |
| Lab Operations adapter | LXC 104; running SHA-256 `0730cd25575ce2b0c5c632e8b106fd3d48cb03cf0a64df9c44e275238d4e4499` | Byte-identical to `007ef82` source; no adapter deployment needed for SA0 |
| Gateway configuration | Request timeout 180 seconds; ordinary response cap 500; four tool rounds configured; directory-first retrieval enabled; model name `qwen3.8-27b` | Non-secret values captured; health-specific cap and other defaults require later code/config review |
| Inference server | LXC 110; `aster-llama` active; llama.cpp build 11081, commit `161755f29`; Vulkan; 8K context; one slot; Qwen3.8-27B UD-IQ4_XS; all layers offloaded | Reasoning remains explicitly disabled: `--reasoning off --reasoning-budget 0` |
| Inference binary | SHA-256 `47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693` | Matches the accepted B60 engineering record; retain as the initial comparison baseline |
| Model artifact | Two shard paths under `/opt/models/qwen3.8-27b-iq4xs/`; direct full hashing was intentionally not repeated because it would impose avoidable read load on the live inference host | Identify immutable artifact manifest/accepted prior digest before SA3; do not substitute a model based on a filename alone |

The gateway source diff is confined to later Companion/AI-PAM user-interface and
fresh-passkey behavior: the management control has ARIA expanded state and toggles
closed; management reads session passkey status; explicit sign-in and management
reauthentication enter Aster's dedicated passkey flow. These behaviors match the
omitted local commits `3401eef`, `efd1871`, `df37352`, `23eccd8` and `8630113`.
The live gateway hash did not map to any inspected committed blob, so it remains a
separate exact-source reconciliation item even after the local history is merged.
The current published gateway source hash is
`f3d460fbf0af81befc1e296a6f518fdc6b7e5cb11c3eb189d1c905b7c695bddb`.

## Decision and next safe action

Do **not** deploy the published `aster_agent.py`, restart `aster-agent`, enable
reasoning, alter the context window or replace model files. Any of those could
discard accepted Companion security/usability behavior or alter the production
baseline before it has been measured.

Next, merge the omitted local production history and publish the reconciled history.
Then derive a reviewed candidate from the running gateway source or a recoverable
source checkpoint, apply the now-reconciled work intentionally, and bind the
candidate to an immutable release manifest. Then implement read-only SA1/SA2 in an
isolated candidate path. The model baseline, live source diff and current response
caps must remain recorded for SA3's current-versus-improved comparison.

## Evidence limits

This is a source/runtime manifest, not a full service audit. It does not validate
every environment variable, model shard digest, Companion workflow, broker invariant
or production capability. Values that could disclose credentials were not read.
