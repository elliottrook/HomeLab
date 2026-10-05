# V3 invented-fixture isolation candidate

Status: **local source only; not executed**. This candidate contains one invented
negative-control fixture and no accepted routing corpus, credentials, network
attachment, model call, tool call, or infrastructure authority.

## Question

Can a fresh, disposable, networkless Debian VM enforce the minimum worker boundary
needed by S0: no network socket creation, no child creation, no unrelated canary
read, no system write, a scrubbed environment, an unprivileged identity, bounded
resources, and a parent-owned result path?

The outcome is binary per check. A missing, malformed, false, oversized, duplicated,
or unbound result is a failure. Passing this probe establishes only the tested
boundary on the pinned image and unit. It does not authorize or validate the
accepted corpus, router quality, privacy classification, or production use.

## Boundary and flow

The hypervisor gives the VM no virtual NIC, guest agent, shared directory,
passthrough device, credential, or login key. Cloud-init creates a locked system
user, a planted non-secret canary, an output directory, the pinned probe, and the
systemd unit. The unit adds a private network namespace, syscall denial for network
I/O and fork/clone, strict system protection, an inaccessible canary path, a single
task, 64 MiB memory, no swap, 10% CPU, 8 KiB file limit, and 15-second deadline.

The invented Python probe attempts each prohibited operation and records only
errno-based outcomes. It publishes a bounded canonical JSON result through the
same chunked serial protocol proven by V2b. The outer cloud-init process copies the
already-written protocol to the serial console and powers the VM off even when the
unit reports a failed check. The local parser must bind the exact run and payload
manifest, require every expected Boolean to be true, and reject extra fields.

## Freshness and execution gate

Execution must use a newly imported image disk and a new cloud-init instance ID;
VM119's booted disk is not reusable. Current planning identity is VM120, subject to
a fresh `nextid` and absence check. The reviewed release must create the VM stopped,
validate its complete config, then stop for an explicit one-run approval. One boot,
one bounded serial capture, no retry. Failure leaves the VM stopped and retained.

No cleanup, deletion, accepted-corpus access, network attachment, credentials,
package installation, service deployment, policy change, or Git push belongs to
V3. Those require separate scope where applicable.

## Acceptance evidence

- all candidate and release hashes match the reviewed manifest;
- the ISO contains exactly `user-data` and `meta-data`;
- strict stopped-config validation passes with no `netN` or unexpected device;
- exactly one well-formed protocol result binds `isolation-fixture-001` and its
  payload digest;
- every declared check is true and `corpus_evaluated` remains false;
- capture remains at or below 1 MiB and completes within 300 seconds;
- VM120 is stopped after the run; and
- pre/post guest inventories show no unrelated lifecycle change.

If any condition fails, V3 is inconclusive or failed. It does not silently weaken
controls or fall back to an ordinary subprocess.
