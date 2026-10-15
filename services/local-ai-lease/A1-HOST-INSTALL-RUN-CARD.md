# A1 host installation and run card

Status: reviewable live-change request; **not deployed**. This card is for
the application-only benchmark and is separate from the 03:15 full-stop
recovery drill.

## Fixed deployment identity

Source identity: **stream-a-candidate-path-baseline** at candidate commit
`e6b638e4`. This first A1 result is not a production Aster measurement. The
final receipt and result label must preserve that distinction. The candidate
import closure and requirements manifest are documented in
`A1-Aster-source-bundle-inventory-2026-10-14.md`; the installed dependency
wheel versions/hashes remain a live preflight gate. If the exact candidate
closure and reproducible dependency environment cannot be installed, do not
start the sidecar.

| Item | Required value |
|---|---|
| Guest and unit | LXC 104, `aster-a1-test.service` |
| Service UID | `1904`, dedicated and unprivileged; no `aster`, broker, approval or administrative groups |
| Listener | `192.168.70.10:19104`, non-public; only the named Mini test client may connect |
| Production listener | `192.168.70.10:9120` is not used or proxied |
| Backend | `http://192.168.70.12:11435/v1`, exact accepted llama.cpp b11429 SYCL/Level-Zero profile |
| Worker/deadlines | one worker; response cap `256`; tool rounds `0`; request timeout `60` seconds |
| Batch | 20 frozen fictional request digests, one attempt each, maximum 20 minutes (`max_wall_s=1200`) |
| Lease | `application-b60-exclusive-v1`; distinct source-bound application backup receipt |

The sidecar must not read the production Aster environment, OpenBao material,
broker/approval sockets, privileged mounts, household knowledge, Doctor
evidence or production state. Its knowledge directory is empty and its durable
attempt/ASGI-clock directories are owner-only and outside Git.

## Credentials and custody

Three fresh test-only values are generated during installation: ingress bearer,
inner Aster key and backend key. The current llama.cpp service authenticates
from `/etc/aster-llama-api-keys` in LXC110 and supports multiple keys. The
bounded topology therefore appends one new, labelled test key to that existing
root-owned file without changing or printing the production key, then performs
one controlled `aster-llama.service` restart so llama.cpp rereads the file. The
sidecar receives the same test key through its protected credential file. This
is an explicit, reversible LXC110 key-file modification and service restart;
the key file, binary, model, device, port and backend settings otherwise remain
unchanged.

The three test-only values are stored only in protected credential files; they
are never committed, printed, placed in the model prompt or included in the
exported receipt. The host preflight compares local SHA-256 digests to prove
that the three values are distinct and that none equals a production
credential. The sidecar process must not inherit `CREDENTIALS_DIRECTORY` for
production material or any production environment file.

## No-effect preflight

Before installing, enabling, stopping or starting anything, the platform owner
must capture a source-bound **application backup checkpoint** and verify all of
the following read-only facts. This is not a lease receipt: no leased state is
claimed yet, and Stream A must not manufacture a preview receipt from it.

1. LXC110 `aster-llama.service` is active, its exact binary/model/device
   hashes match the accepted b11429 manifest. This is planned backend identity
   only; it does not claim exclusivity before the temporary ingress policy is
   applied and observed later.
2. LXC104 and LXC116 production consumers are healthy before the checkpoint;
   the application controller's allowlist is exactly `(104, aster-agent.service)`
   and `(116, aster-speech.service)`.
3. The proposed unit is disabled and absent from the process table, port
   `19104` is unused, no sidecar state/lock exists, and no A1 credential or
   evidence directory is present.
4. The existing LXC110 key file is backed up as a root-only checkpoint without
   reading key values into the operator session. The proposed test-key line is
   absent, and the current production key authenticates an actual
   `/v1/chat/completions` request. `/v1/models` alone is not an auth test.
5. The host controller has generated a planned lease ID/generation in its
   protected pre-lease plan, distinct from the full-stop recovery lease. The
   plan is an input to acquisition, not evidence that a lease is active.
6. At least 35 minutes remain before the 04:15 restoration deadline: up to 20
   minutes for the frozen batch plus the 15-minute restoration reserve. Any
   preflight/setup time must fit before this gate.

Any failed check means zero service effects and zero model calls.

## Bounded installation and run

Only after the no-effect preflight passes, the platform owner may perform this
single bounded change:

1. Install the pinned `a1_isolated_app.py` factory and its exact dependency
   bundle, the strict final config file containing the 20 frozen A1 request
   digests, unit, owner-only empty data directories, test-only credentials and
   host observer. The factory must reject bad config before importing Aster.
   Keep the unit disabled until all files and digests are checked.
2. Install a separate disposable probe gateway/config with its own 20
   fictional probe-body hashes, disposable journal and probe credentials. The
   probe gateway and its hashes must be distinct from the final A1 gateway;
   no final A1 body may be consumed by a startup or denial probe.
3. Acquire the application lease from the protected pre-lease plan. The host
   controller persists an **armed** state with start-by and restore deadlines
   before stopping any consumer. The controller may stop/runtime-mask only
   LXC104 Aster and LXC116 Speech. It must not change LXC110 beyond the
   later checkpointed application effects. A crash after any subsequent effect
   is therefore recoverable by the application watchdog.
4. Append the generated test backend key to the existing LXC110 key file
   using an atomic immutable-checkpoint update, restart `aster-llama.service`
   once, and verify the old production key still works, the new test key works,
   and a wrong key receives 401 on the actual chat endpoint. This effect is
   under the already-armed application watchdog.
5. Apply a temporary, checkpointed LXC110 ingress policy allowing only source
   `192.168.70.10` to TCP 11435. This is the sidecar's source address; it
   excludes Mac/LAN clients and other guests. Verify policy read-back and test
   from an excluded listening client before admitting the sidecar. The previous
   policy must be restorable byte-for-byte.
6. After the application receipt producer records the persisted armed lease,
   validate the newly produced receipt, including lease ID/generation,
   application backup binding, watchdog deadline, active backend,
   `exclusive_backend_claim=true`, `backend_listener_ipv4_only=true`, and
   consumer quiescence. The claim is true
   only when the temporary ingress policy is active and observed; zero load at
   one instant is not evidence. If the receipt is absent or invalid, make zero
   model calls.
7. Start `aster-a1-test.service` as UID 1904 with the disposable probe journal
   and probe credential fixture. The host observer must attest the
   exact PID, UID, one worker, port 19104, source/dependency digests and lease
   identity before any request is sent. These probes are not the benchmark
   run and their frozen request bodies must not be reused.
7. Run the denial probes below. A single unexpected allow, second worker,
   source mismatch or missing durable observation aborts the run before the
   20-request batch. Prove that the disposable probe journal contains no
   backend calls, stop the probe instance, securely remove its disposable
   journal/fixture, and create a fresh owner-only journal and fresh run
   credential handoff.
8. Start the final run instance from the clean owner-only journal and run the
   frozen 20-request control batch through the sidecar. Record only
   content-free observation IDs, timing/status fields, request digests and
   host-attested lease fields. The Mini capture bridge must be exactly
   `a1_full_path_capture.py` SHA-256
   `7141dd938b9a9994523e1eea2ac8078bbd93639ee2459c89dae0589651556157`;
   include that client artifact hash in the final receipt.

## Required denial probes

Each probe must fail without a backend call and be represented in the
host-owned observation, not merely inferred from source code. The wrong-inner,
missing-journal, duplicate-body and other startup/credential probes run only
against the disposable probe instance/journal. They never consume a frozen
final-run request and never write the final owner-only journal:

- wrong ingress bearer;
- `/v1/chat/completions` with a query string;
- any path other than the exact POST endpoint;
- extra tool or non-empty tool list;
- changed request body and repeated request body;
- second worker/process or a second listener;
- missing/unwritable durable journal or ASGI-clock directory;
- wrong-inner-key behavior is tested only with a disposable misconfigured
  factory/app fixture or an inner FastAPI auth check; the admitted final
  process has no separate inner listener. Its live proof is that the gateway
  strips caller identity and replaces it with the configured inner test key,
  while the disposable wrong-inner fixture makes no backend call;
- wrong backend key and missing backend key (actual chat endpoint must return
  401; `/v1/models` is not sufficient);
- read/open attempt for production environment, OpenBao, broker/approval
  socket, privileged mount or household knowledge path;
- TCP/HTTP attempts to Authentik, OpenBao, a known listening non-backend LAN
  destination, Internet/cloud endpoints and the production Aster listener.

The only permitted network destinations are loopback and
`192.168.70.12:11435`. Network denial evidence must include a live packet
policy observation: capture nftables policy counters/logs before the probes,
run the disposable denied-destination attempts, and capture the counters/logs
afterward showing the denied packets. At least one denied check must target a
known listening service (for example the live Authentik/OpenBao endpoint), so
connection refusal cannot be mistaken for egress enforcement. Then issue one
allowed authenticated backend request and show its successful response and
unchanged denial counters for unrelated destinations. A systemd or nftables
declaration without these before/after observations is not evidence.

## Recovery and rollback checkpoint

The sidecar must stop before the 15-minute restoration reserve. The
application-mode watchdog owns recovery in this exact order: stop the sidecar,
restore the checkpointed LXC110 ingress policy, remove the temporary backend
key, reload llama.cpp, verify production authentication and wrong-key denial,
then restore/unmask only LXC104 `aster-agent.service` and LXC116
`aster-speech.service`. If any step or postcheck is uncertain, retain the
lease and do not execute a later step.

The watchdog then verifies:

- LXC110 llama.cpp stayed active throughout and still exposes the accepted
  model/device/backend;
- the temporary LXC110 ingress policy was restored from its checkpoint and its
  normal production sources are admitted again; this is proven with policy
  read-back and counters, not assumed from a restart;
- the dedicated test key remains present only until the benchmark is complete,
  and the production key continues to authenticate;
- Aster and Speech are active and healthy;
- the sidecar port/process/credentials and temporary lease are gone or
  explicitly retained for reconciliation if an effect is uncertain;
- scheduled backup/digest state is unchanged; and
- the application receipt closes as restored, or the watchdog remains the
  recovery authority and the lease is left open for operator reconciliation.

The credential rollback is explicit: remove only the dedicated test-key line
from the checkpointed LXC110 key file, atomically replace the file, restart
`aster-llama.service` once, and revalidate the production key plus wrong-key
401. If that restart or validation is uncertain, retain the root-only
checkpoint and leave the lease open for platform reconciliation; do not guess
that authentication was restored.

The backend-claim rollback is equally explicit: restore the checkpointed
LXC110 ingress policy, verify the normal production source set and deny the
sidecar-only test path after the lease, then close the application receipt.

No application benchmark result is accepted if the sidecar, network, receipt,
watchdog or restoration proof is incomplete. The full-stop recovery drill is
reported separately and cannot satisfy this card's application-mode evidence.

## Bounded live change request

Requested later approval: install the pinned A1 sidecar bundle and host
observer in LXC104, create the dedicated UID/port and test-only credential
files, append one fresh test backend key to the existing LXC110 multi-key file,
perform one controlled llama.cpp restart, perform the no-effect preflight,
acquire one application-only lease, run the denial probes and at most one
20-request synthetic batch, then remove the test key and perform the documented
restoration. Scope excludes model/backend changes, production credentials,
OpenBao changes, new public ingress, network broadening, Git push and the
03:15 full-stop recovery drill. The LXC110 key-file append and restart are
explicitly in scope and are the only LXC110 mutation.
