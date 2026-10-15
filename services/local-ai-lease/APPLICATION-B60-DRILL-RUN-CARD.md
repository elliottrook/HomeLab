# Application-only B60 watchdog/recovery drill card

Status: offline drill proposal; not authorized or scheduled. This is separate
from the paused 03:15 full-stop drill and from the later 20-call A1 benchmark.
No clock slot authorizes this card.

## Purpose and hard boundary

Prove that the application-only lease can drain only Aster Agent and Aster
Speech, preserve the accepted LXC110 llama.cpp backend, and independently
restore the sidecar, ingress policy, temporary test key and consumers. The
watchdog must release nothing until exact runtime, authentication, GPU/model,
and six-point schedule checks pass.

The application lease must contain separate `restore_start_epoch` and
`restore_deadline_epoch` values, at least 900 seconds apart, with the hard
deadline no later than 04:15 Vancouver. A1 work may not begin unless at least
35 minutes remain before that deadline.

## Read-only/offline gates — can be completed before the drill

- Run the focused controller, watchdog, trusted-observer, receipt-boundary and
  backup-adapter tests.
- Verify the disabled LXC104 sidecar receipt, exact source/wheel/unit hashes,
  UID1904, absent credential, inactive unit and absent listener.
- Verify Proxmox controller/watchdog destination absence or the approved
  disabled hashes without enabling or starting them.
- Verify LXC110's accepted Qwen3.5-9B Q4_K_M model, b11429 SYCL binary, unit
  hash and GPU device read-only.
- Verify the current-cycle backup receipt: Proxmox artifacts, TrueNAS LXC110
  mirror, and Mac `source-destination-exact-subset` receipt. The Mac receipt
  must bind the pinned subset manifest and equal source/destination facts to
  task-2 start/finish; `tree-present-only` is insufficient.
- Verify News and backup schedule metadata, lease timing, and the observer's
  pinned host key. These checks do not prove consumer quiescence.

## Live actions requiring one new explicit drill approval

| Action | Why it is live | Required proof/rollback |
|---|---|---|
| Arm application lease and host lock | Creates effect authority and persistent lease state | Lease ID/generation, reserve epochs, source-bound backup receipt; retain lock on ambiguity |
| Stop/runtime-mask LXC104 Agent and LXC116 Speech | Changes production consumers | Two quiescence samples; restore exact prior states on failure |
| Add disposable LXC110 test key | Changes backend authentication state | Separate checkpoint, intent/observed journal, remove before release |
| Apply temporary LXC110 ingress ACL | Changes network admission | Exact source `192.168.70.10` → TCP 11435 only; restore checkpointed policy |
| Start the disabled A1 sidecar | Creates the test endpoint | UID1904, one worker, credential/network denial probes, exact endpoint; stop on failure |
| Trigger watchdog recovery | Tests independent restoration | Owner-loss/expiry or bounded recovery trigger; verify every fixed observer probe |

The drill may use a zero-model-call recovery path. Starting the sidecar alone
does not authorize a backend request. A later 20-call A1 benchmark needs a
separate approval after the recovery drill passes.

## Authenticated callback contract

The platform callback must read a current host-owned
`ApplicationReceipt` through the authenticated receipt boundary and project it
with `application_receipt_boundary.admission_payload`. It must return exactly:

```json
{
  "schema": "aster-a1-admission.v1",
  "lease_id": "<current lease>",
  "generation": 1,
  "receipt_sha256": "<digest of canonical host receipt>",
  "profile_sha256": "<pinned A1 profile>",
  "endpoint": "http://192.168.70.10:19104/v1/chat/completions"
}
```

The Mini runner rechecks this payload before the batch and before every
possible model call, requires stable lease ID/generation, and writes the
receipt digests into the owner-only final manifest. A caller-supplied boolean,
arbitrary endpoint, fabricated receipt, or stale lease is rejected.

## Recovery success criteria

The watchdog may only produce a releasable receipt after:

- sidecar stopped and no listener remains;
- temporary key removed and production auth succeeds while the wrong key is
  denied;
- checkpointed ingress policy is restored;
- Aster Agent and Speech are restored to their prior states;
- LXC110 service is active with exact b11429 binary, Q4_K_M model, unit hash,
  GPU visibility and authenticated generation;
- Proxmox, TrueNAS guest/LXC110/Mac and News schedule points match the pinned
  six-point schedule;
- the lease identity, generation and source-bound backup receipt remain bound.

Any failed or uncertain check retains the lease lock and recovery journal for
operator reconciliation. It must not be reported as `READY`.

## Explicit exclusions

This card does not authorize the 03:15 full-stop drill, host reboot, LXC110
llama stop/restart, production key access, permanent ACL or schedule changes,
News changes, the 20-call A1 batch, arbitrary model prompts, or Git push.

## Rollback

Stop the sidecar, remove the temporary key, restore the ingress checkpoint,
restore the two consumers to their recorded prior states, and run every exact
postcheck. If any step is uncertain, retain the lock and raw content-free
journal, do not replay blindly, and stop for operator reconciliation.
