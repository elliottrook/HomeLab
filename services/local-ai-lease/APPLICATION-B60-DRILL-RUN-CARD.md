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
| Stop LXC104 Agent and LXC116 Speech | Changes production consumers; the current controller does not runtime-mask them | Two quiescence samples; restore exact prior states on failure |
| Add disposable LXC110 test key | Changes backend authentication state | Fixed `aster-llama-test-key-add` wrapper, immutable checkpoint, intent/observed journal, remove before release |
| Apply temporary LXC110 ingress ACL | Changes network admission | Fixed `aster-llama-ingress-apply` wrapper; exact source `192.168.70.10` → TCP 11435 only; restore checkpointed policy |
| Start the disabled A1 sidecar | Creates the test endpoint | UID1904, one worker, credential/network denial probes, exact endpoint; stop on failure |
| Trigger watchdog recovery | Tests independent restoration | Owner-loss/expiry or bounded recovery trigger; verify every fixed observer probe |

The current recovery candidate is not a zero-model-call path. The key effect
must be applied by the fixed wrapper before sidecar start; the wrapper reads
only the owner-only test-key file and emits no key material. Once the
temporary key is removed, it performs one planned `systemctl restart
aster-llama.service`; the trusted observer's exact backend check, the
production-auth probe, and the post-consumer exact check each perform one
bounded authenticated health generation. That is a maximum of three tiny
health generations, with no arbitrary prompts; the wrong-key denial is an HTTP
401 check and is not a generation. The backend is unavailable only during the
planned restart and must return with the exact postchecks. The pre-run key
activation and its bounded backend restart are a separate live packet item:
they must be installed, observed and counted before the sidecar starts, with
the same exact backend postchecks. A later 20-call A1 benchmark
needs a separate approval after the recovery drill passes.

## Authenticated callback contract

The trusted host controller must call `record_owner_receipt` after its fixed
observer checks, and the watchdog must call `write_watchdog_status` after each
current recovery assertion. The platform callback must then load the current
host-produced `ApplicationReceipt`
from the fixed root-owned mode-0600 path
`/var/lib/local-ai-lab/application-b60/application-receipt.json`, read the
current lease state and lock, and read the current watchdog status. It must
then project it with `application_receipt_boundary.active_admission_payload`.
The boundary pins
profile `7caddc30074f5925722861c59f70733894037b9fc5b0865feb98bf9e08bbbfec`,
sidecar bundle `969b6db34e8fe0c00e9a5be6163a498bae5ccfd101e42f699bfafb39f4a8c403`,
UID 1904, port 19104 and the exact endpoint. It rejects a caller-created
receipt, arbitrary profile, alternate sidecar, released lease, mismatched
generation, missing lock, or stale watchdog. It must return exactly:

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

Drill helper pins: key add `10292b91e79ebe30892ef3ce0f9af70a4ecf52b523878d7fd4c1cc8099cca156`,
key status `9fa646d7db2974389cbea18a68edd82a868b849fcfdd435578e28d729403c9cf`,
key remove `0c294198d2e60b5ed07654c92025713ca6a812bdd065720f3d8183ae6ef357d6`,
ingress apply `41b96f560261a198c09fd85d8ba7150478241fbe6a38f28befad9dc4fa40020b`,
and ingress restore `9bf3c3cb1e04081f41584f9dc742d86e9e7ead3a1806a243a6ce3478572ff347`.
These are a separate drill candidate and are not part of the frozen disabled-
install packet.
The current drill-only receipt boundary source hash is
`dcde70b9d00fdb2d9b37edef7edbe441b2a3ba24e21ac2a341eb7a8cf4933bf7`, and the
watchdog status producer hash is
`3447d490ec396dee45191a5294537f2132deac6578e3e30376f6f6980a98e8d2`.
The LXC110 helper package must include `a1_key_file.py` hash
`25f2c82cb09b051f3307341571b3a27c6b2c4f6002c70b5a1a256ed4e8292b36` before
the key wrappers can be installed. These producer/helper files are drill-only
candidate artifacts and are not part of the frozen disabled-install packet.

## Recovery success criteria

The watchdog may only produce a releasable receipt after:

- sidecar stopped and no listener remains;
- temporary key removed and production auth succeeds while the wrong key is
  denied;
- the one planned backend restart (if the key effect was observed) has a fresh
  active-state and exact-runtime postcheck;
- checkpointed ingress policy is restored;
- Aster Agent and Speech are restored to their prior states;
- LXC110 service is active with exact b11429 binary, Q4_K_M model, unit hash,
  GPU visibility and authenticated generation;
- Proxmox, TrueNAS guest/LXC110/Mac and News schedule points match the pinned
  six-point schedule;
- the lease identity, generation and source-bound backup receipt remain bound.

Any failed or uncertain check retains the lease lock and recovery journal for
operator reconciliation. It must not be reported as `READY`.

The key/ingress helper set is now concrete and pinned for the drill candidate:
`aster-llama-test-key-add`, `aster-llama-test-key-status`,
`aster-llama-test-key-remove`, `aster-llama-ingress-apply`, and
`aster-llama-ingress-restore`. The wrappers must be installed root-owned with
mode 0755 beside the recovery helper and must remain disabled/not auto-run.

## Explicit exclusions

This card does not authorize the 03:15 full-stop drill, host reboot, any
unplanned LXC110 stop/restart, production key access, permanent ACL or
schedule changes, News changes, the 20-call A1 batch, arbitrary model prompts,
or Git push. Installation of the drill-only helper package, its pre-run key
activation/restart, and the live effect window still require one bounded
approval and must not be inferred from this card.

## Rollback

Stop the sidecar, remove the temporary key, restore the ingress checkpoint,
restore the two consumers to their recorded prior states, and run every exact
postcheck. If any step is uncertain, retain the lock and raw content-free
journal, do not replay blindly, and stop for operator reconciliation.
