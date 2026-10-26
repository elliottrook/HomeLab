# Stream A candidate-H and F4/F5 admission binding proposal

**Date:** 2026-10-25  
**Decision:** source contract ready for platform implementation; live F6 remains **NO-GO**

This proposal closes the specification gaps found in the platform owner's
effectful F6 card without changing the platform repository or the live host.
It supersedes candidate-G as the proposed D4 workload, but it does not transfer
candidate-G's authorization and does not authorize candidate-H, M3, a lease,
consumer quiescence or a model call.

## Measured starting point

Candidate-H is installed in LXC104 under the dedicated non-login identity
`aster-d4-eval` (UID/GID 977) with no supplementary groups. Its second inactive
staging attempt passed target-Linux custody, negative credential-access and
fictional descriptor-delivery checks with zero model calls and zero credential
reads. The fixed installed objects are:

| Object | Installed identity |
|---|---|
| immutable packet | `/var/lib/aster/d4-candidate-h`, root:`aster-d4-eval` `0750`; exactly 11 root:`aster-d4-eval` `0640` files |
| private output | `/var/lib/aster/d4-candidate-h-output`, `aster-d4-eval`:`aster-d4-eval` `0700`; empty |
| launcher | `/usr/local/libexec/aster-d4-candidate-h-launcher`, root:root `0755`, SHA-256 `71c07060a59a81923803fdd21cc14f218fc3c1c1f7f1797e1b1e75acdf4240eb` |
| unit | `/etc/systemd/system/aster-d4-candidate-h.service`, root:root `0644`, SHA-256 `76c0ba89b26124b1e0fb74e3ddc761a001d937195c4d14ce0c3b5ab0d6b62450` |
| identity fragment | `/usr/lib/sysusers.d/aster-d4-eval.conf`, root:root `0644`, SHA-256 `c4bfc0aa4446d77c252f9cd233842ac101e849ddeddf4347ad30d80298410c64` |

The service is static and inactive. Its unit deadline is 2,250 seconds and the
launcher deadline is 2,200 seconds. The launcher validates all packet bytes,
the Python 3.13 interpreter, fixed identity and empty output directory; root
opens `/etc/aster/aster.env`, extracts the one bounded key, passes it through an
inherited pipe descriptor and drops the child to UID/GID 977 with no
supplementary groups. The child receives no API key in argv or environment and
cannot reopen the credential file. Candidate-H's run digest is
`423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4`.

The exact workload invocation is frozen inside the launcher as:

```text
/opt/aster-agent/venv/bin/python
/var/lib/aster/d4-candidate-h/sa3_development_execute.py
--fixtures /var/lib/aster/d4-candidate-h/sysadmin-sa3-development-fixtures-draft-v1.json
--source-corpus /var/lib/aster/d4-candidate-h/sysadmin-incident-development-extension-draft-v1.json
--source-plan /var/lib/aster/d4-candidate-h/sysadmin-incident-development-plan-v1.json
--expected-run-digest 423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4
--ledger /var/lib/aster/d4-candidate-h-output/attempt-journal.jsonl
--execute
--key-fd <inherited descriptor>
```

The current platform evaluation entrypoint accepts an exact acquire object
containing backup, F2 and F3 receipt strings. It rejects any F4/F5 field. The
separate full-stop candidate can read the F4 pre-acquire receipt, but the
Stream A evaluation lease neither validates nor durably records the F4 digest,
and no durable F5 observation producer exists. Therefore prose that says the
lease is “bound to F4/F5” is not executable.

## Required platform-owned admission artifact

The platform owner should add one root-owned, mode-`0600`, non-symlink regular
file at the fixed path:

`/var/lib/local-ai-lab/stream-a-evaluation/admission.json`

Its parent remains root-owned mode `0700`. The file must have one link, be
opened with `O_NOFOLLOW`, be bounded to 16 KiB, reject duplicate JSON keys and
use this exact versioned object:

```json
{
  "schema": "stream-a-evaluation-admission-v1",
  "cycle_date": "YYYY-MM-DD",
  "lease_id": "<fixed generated lease ID>",
  "generation": 1,
  "created_epoch": 0,
  "expires_epoch": 0,
  "backup_receipt": "retained-archive-integrity-sha256:<64 hex>",
  "f2_result_sha256": "<64 hex>",
  "f3_receipt_sha256": "<64 hex>",
  "f4_receipt_sha256": "<64 hex>",
  "f5_observation_sha256": "<64 hex>",
  "d4_run_digest": "423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4",
  "m3_manifest_sha256": "69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165",
  "model": "Qwen3.5-9B-Q4_K_M",
  "backend": "llama.cpp-b11429-SYCL-Level-Zero"
}
```

The displayed zero epochs are schema placeholders only; a produced artifact
must use positive integer values, must not be future-dated, and must expire no
more than 15 minutes after creation. It must be fresh when `acquire` persists
`PREPARED`; the durable lease then binds its digest for the rest of the
transaction. Later phases compare the retained digest and custody but do not
incorrectly require a 15-minute pre-acquire observation to remain fresh for a
90-minute lease.

The producer must independently open and hash the exact accepted F2 terminal
result, F3 retained receipt, F4
`/var/lib/local-ai-lab/pre-acquire-receipt.json` and a new F5 observation. It
must prove they identify the same backup cycle, lease ID and generation before
writing the admission atomically. It must never infer sameness from filenames
or schedule time.

The F5 observation must be a second root-owned mode-`0600` bounded artifact at
`/var/lib/local-ai-lab/stream-a-evaluation/f5-observation.json`. Its versioned
schema must carry the cycle date, F2/F3/F4 digests, LXC110 mirror completion
identity, current schedule-set digest, accepted model/binary/unit/auth
identities, exact four-consumer baseline, absence of a conflicting lease or
job, observation epoch and an expiry. It carries observations and digests only;
it cannot claim isolation, create a lease or authorize an effect.

## Required controller binding

The evaluation acquire intent must add exactly one field:

```json
"admission_receipt": "stream-a-evaluation-admission-sha256:<64 hex>"
```

Before durable `PREPARED` state, the fixed entrypoint must open the fixed
admission path, verify custody and exact schema, compute the canonical file
SHA-256 and compare it to `admission_receipt`. It must also require:

1. fresh creation and expiry epochs;
2. exact lease ID and generation agreement;
3. exact backup/F2/F3 agreement with the other acquire fields;
4. exact accepted model/backend agreement;
5. the fixed candidate-H and M3 digests above; and
6. the same-cycle F4 and F5 cross-bindings.

The validated admission digest must be stored in durable lease state and
preserved through `PREPARED`, `QUIESCING`, `RUNNING`, workload outcomes,
restoration and content-free close-out. `post-quiescence` must revalidate the
same bytes, digest and custody without applying a second freshness window; a
missing, changed or foreign artifact is fail-closed and enters recovery if
consumer effects have begun.

Do not overload `f3_receipt`, use an unvalidated path supplied by the operator,
or place the entire artifact in an intent. Those alternatives either erase the
F4/F5 distinction or permit the live operator to select evidence at execution
time.

## D4 and M3 effect sequence after admission

The future effect card must replace every candidate-G reference with the
candidate-H service, digest and output paths above. After a durable `RUNNING`
lease and a recorded D4 `start`, the fixed action is one
`systemctl start aster-d4-candidate-h.service` in LXC104. Terminal acceptance
requires a zero service result, an exact bounded journal in the private output
directory, the fixed digest, complete structural checks, no transport
uncertainty and remaining restoration reserve. There is no automatic retry.

Only then may the already frozen M3 command run in LXC110 under its fixed
Python 3.13.5 identity, 1,230-second timeout, staged manifest and key-file
boundary. The lease bookkeeping `start` and `outcome` calls surround each real
runner; they do not replace it.

Recovery must independently prove restoration of the four consumer units,
accepted llama.cpp/SYCL health and GPU holder, News timers, all lease and
operation locks, owner heartbeat, watchdog state, intent files and the exact
prestate. Admission, F4/F5 and workload evidence are retained until that
postcheck is complete. Cleanup cannot silently delete an uncertain result.

## Implementation and review gate

The Local AI platform project owns the controller, entrypoint, admission
producer and live release card. Its next deliverable is a source-only change
and tests covering exact schemas, custody, cross-cycle substitution, stale
evidence, duplicate keys, digest mismatch, lease/generation mismatch,
durable-state round trip and recovery after a post-validation failure. It must
then produce a new inactive-install card with full installed paths, hashes,
rollback and target-Linux tests.

Until that change is independently reviewed and installed inactive, F6 remains
**NO-GO**. The October 26 F2 timers are independent and must not be altered by
this work.
