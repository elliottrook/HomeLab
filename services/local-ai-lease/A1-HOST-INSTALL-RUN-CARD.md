# A1 host installation and run card

Status: reviewable live-change request; **not deployed**. This card is for
the application-only benchmark and is separate from the 03:15 full-stop
recovery drill.

## Fixed deployment identity

| Item | Required value |
|---|---|
| Guest and unit | LXC 104, `aster-a1-test.service` |
| Service UID | `1904`, dedicated and unprivileged; no `aster`, broker, approval or administrative groups |
| Listener | `192.168.70.10:19104`, non-public; only the named Mini test client may connect |
| Production listener | `192.168.70.10:9120` is not used or proxied |
| Backend | `http://192.168.70.12:11435/v1`, exact accepted llama.cpp b11429 SYCL/Level-Zero profile |
| Worker/deadlines | one worker; response cap `256`; tool rounds `0`; request timeout `60` seconds |
| Batch | 20 frozen fictional request digests, one attempt each, maximum 10 minutes |
| Lease | `application-b60-exclusive-v1`; distinct source-bound application backup receipt |

The sidecar must not read the production Aster environment, OpenBao material,
broker/approval sockets, privileged mounts, household knowledge, Doctor
evidence or production state. Its knowledge directory is empty and its durable
attempt/ASGI-clock directories are owner-only and outside Git.

## Credentials and custody

Three fresh test-only values are generated during installation: ingress bearer,
inner Aster key and backend key. They are stored only in the root-owned host
checkpoint/credential handoff and the service's protected credential files;
they are never committed, printed, placed in the model prompt or included in
the exported receipt. The host preflight compares their local SHA-256 digests
to prove that the three values are distinct and that none equals a production
credential. The sidecar process must not inherit `CREDENTIALS_DIRECTORY` for
production material or any production environment file.

## No-effect preflight

Before installing, enabling, stopping or starting anything, the platform owner
must capture a source-bound application receipt and verify all of the following
read-only facts:

1. LXC110 `aster-llama.service` is active, its exact binary/model/device
   hashes match the accepted b11429 manifest, and no other inference consumer
   owns the backend lease.
2. LXC104 and LXC116 production consumers are healthy before the checkpoint;
   the application controller's allowlist is exactly `(104, aster-agent.service)`
   and `(116, aster-speech.service)`.
3. The proposed unit is disabled and absent from the process table, port
   `19104` is unused, no sidecar state/lock exists, and no A1 credential or
   evidence directory is present.
4. The lease receipt is application mode, has a new lease ID/generation, binds
   the backup receipt and watchdog deadline, and is not derived from the
   full-stop recovery receipt.
5. At least 15 minutes remain before the 04:15 restoration deadline.

Any failed check means zero service effects and zero model calls.

## Bounded installation and run

Only after the no-effect preflight passes, the platform owner may perform this
single bounded change:

1. Install the pinned sidecar source/dependency bundle, unit, owner-only empty
   data directories, test-only credentials and host observer. Keep the unit
   disabled until all files and digests are checked.
2. Acquire the application lease. The controller may stop/runtime-mask only
   LXC104 Aster and LXC116 Speech. It must not stop, restart, mask or reconfigure
   LXC110 llama.cpp.
3. Start `aster-a1-test.service` as UID 1904. The host observer must attest the
   exact PID, UID, one worker, port 19104, source/dependency digests and lease
   identity before any request is sent.
4. Run the denial probes below. A single unexpected allow, second worker,
   source mismatch or missing durable observation aborts the run before the
   20-request batch.
5. Run the frozen 20-request control batch through the sidecar. Record only
   content-free observation IDs, timing/status fields, request digests and
   host-attested lease fields.

## Required denial probes

Each probe must fail without a backend call and be represented in the
host-owned observation, not merely inferred from source code:

- wrong ingress bearer;
- `/v1/chat/completions` with a query string;
- any path other than the exact POST endpoint;
- extra tool or non-empty tool list;
- changed request body and repeated request body;
- second worker/process or a second listener;
- missing/unwritable durable journal or ASGI-clock directory;
- wrong inner key;
- read/open attempt for production environment, OpenBao, broker/approval
  socket, privileged mount or household knowledge path;
- TCP/HTTP attempts to Authentik, OpenBao, broker, other LAN services,
  Internet/cloud endpoints and the production Aster listener.

The only permitted network destinations are loopback and
`192.168.70.12:11435`. A systemd or nftables declaration is not evidence until
the live denial attempts fail and the backend request still succeeds.

## Recovery and rollback checkpoint

The sidecar must stop before the 15-minute restoration reserve. The host owner
then stops it, retains any uncertain receipt/journal, restores/unmasks only
LXC104 `aster-agent.service` and LXC116 `aster-speech.service`, and verifies:

- LXC110 llama.cpp stayed active throughout and still exposes the accepted
  model/device/backend;
- Aster and Speech are active and healthy;
- the sidecar port/process/credentials and temporary lease are gone or
  explicitly retained for reconciliation if an effect is uncertain;
- scheduled backup/digest state is unchanged; and
- the application receipt closes as restored, or the watchdog remains the
  recovery authority and the lease is left open for operator reconciliation.

No application benchmark result is accepted if the sidecar, network, receipt,
watchdog or restoration proof is incomplete. The full-stop recovery drill is
reported separately and cannot satisfy this card's application-mode evidence.

## Bounded live change request

Requested later approval: install the pinned A1 sidecar bundle and host
observer in LXC104, create the dedicated UID/port and test-only credential
files, perform the no-effect preflight, acquire one application-only lease,
run the denial probes and at most one 20-request synthetic batch, then perform
the documented restoration. Scope excludes LXC110 service changes, production
credentials, OpenBao changes, new public ingress, network broadening, model
changes, Git push and the 03:15 full-stop recovery drill.
