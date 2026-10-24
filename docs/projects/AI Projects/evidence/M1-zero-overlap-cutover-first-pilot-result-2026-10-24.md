# M1 zero-overlap cutover — first pilot result

Date: 2026-10-24 PDT  
Result: **NO-GO, rolled back before network ingress started**

## Bounded result

The approved pilot reached the first identity-boundary check and stopped on a
real target-Linux failure. The independent broker created its socket as mode
`0660`, owned `hlabroker:aster-approval`, but systemd created the parent runtime
directory as mode `0750`, owned `hlabroker:hlabroker`. The `aster-approval`
identity therefore could not traverse the parent directory. The existing
AI-facing `aster` identity was also denied, as required.

The failure occurred before `aster-approval-ingress.service` was started. Port
9121 never listened, no authenticated Companion call was made, and no approval
or grant was created or consumed.

## Checkpoints and rollback

- A consistent, owner-only broker database checkpoint passed SQLite integrity
  checking before the cutover. Its size was 110,592 bytes and its SHA-256 was
  `8c5da28339d15f87d62f2960f852f0f5d0aa7cef51971379ad45c4c8b183fd85`.
- NPM host 18 received only the longer approval prefix and passed `nginx -t`.
  Aster health remained HTTP 200 while the inactive target failed closed.
- OPNsense received only the temporary NPM-to-LXC104 TCP/9121 rule, adjacent to
  the existing TCP/9120 rule. The configuration helper preserved all unrelated
  XML bytes and retained an owner-only exact backup.
- Rollback removed the NPM location, stopped the independent broker, restored
  the old approval service, removed the temporary firewall rule and reloaded
  both services.
- Post-rollback readback shows NPM's approval location absent, only the original
  firewall rule present, Aster/broker/old approval services active, port 9120
  listening, port 9121 absent, the independent units inactive and Aster health
  HTTP 200.
- The live broker database remains `integrity=ok`, with zero pending and zero
  approved-unconsumed requests.

## First corrective candidate and measured rejection

The first correction added two unprivileged `ExecStartPre` operations and was
installed under a separate approval. On the supervised rerun both commands
exited zero, but systemd reapplied `Group=hlabroker` to the managed runtime
directory before the main process. The directory was again
`0750 hlabroker:hlabroker`; the pilot stopped at the same identity gate and
performed the same complete rollback before ingress started.

The next candidate uses systemd's deterministic runtime-directory control:
mode `0711` on the parent directory and the existing
`0660 hlabroker:aster-approval` on the socket. The parent can be traversed but
not listed or written by other identities; connection authority remains at the
socket, where the AI-facing `aster` identity was already proven denied. This
does not change the database state directory or add permanent group
membership. Six focused tests pass and target `systemd-analyze verify` accepts
the unit. Its exact replacement hash is recorded in the next local commit.

That `0711` candidate was then installed under a separate approval and passed
the live identity boundary: the runtime parent was exactly
`0711 hlabroker:hlabroker`, the socket was exactly
`0660 hlabroker:aster-approval`, `aster` was denied and `aster-approval`
received a valid content-free broker status. The approval-only ingress started
as `aster-approval`, listened only on `192.168.70.10:9121`, returned HTTP 401
locally without a bearer token and had zero restarts.

The pilot stopped at the next network gate. NPM-to-9121 timed out even though
the temporary OPNsense rule was present. Readback showed that the helper had
incorrectly treated firewall sequence numbers as unique and selected `2201`.
The management-interface RFC1918 block is sequence `2200`, so the otherwise
exact rule was unreachable. It recorded evaluations but accepted zero packets.
The route, services and firewall rule were again fully rolled back; 9120 health
remained available.

The corrected temporary-rule helper now clones the established 9120 rule's
sequence `2199` as well as its interface/source/destination properties and
inserts it immediately after that rule. A live read-only check confirms the
source is `2199`, the first management block is `2200`, and no 9121 rule is
present. A further supervised rerun is required to prove the routed path.

## Next gate

The `0711` unit is installed inactive and has passed its live identity test.
Repeat the supervised reversible pilot using only the corrected temporary
firewall placement: sequence `2199`, directly after the established 9120 rule
and before the sequence-2200 block. The rerun must still stop at the first
failed gate and perform the same restrictive rollback.
