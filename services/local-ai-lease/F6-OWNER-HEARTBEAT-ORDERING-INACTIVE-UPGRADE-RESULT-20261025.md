# F6 owner-heartbeat ordering — inactive upgrade result

Status: **INSTALLED INACTIVE; VALIDATED**

At 20:59 PDT on 2026-10-25, the one-file candidate from source commit
`039089695fb8b4cd020f769a90c0b93156e93531` was installed on Proxmox under
the approved inactive upgrade card.

## Installed result

| Target | Installed SHA-256 | Custody |
|---|---|---|
| `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.service` | `7bbb32a64a73b8797f34df934f9f06932c0706f93dc078b08bbc2c737d364f1e` | `root:root 0644`, one regular link |

The replaced unit is preserved at:

`/var/lib/local-ai-lab/checkpoints/f6-owner-heartbeat-ordering-03908969-20261025T2057/stream-a-evaluation-owner-heartbeat.service`

The checkpoint directory is `root:root 0700`; the preserved unit is
`root:root 0600`, one regular link, SHA-256
`6c7777506df7aa2b58e62e3da7fb354859b6487e99441b4445c8a2a537df2ad5`.

## Validation

- `systemd-analyze verify` passed before replacement and again against the
  installed owner, heartbeat and watchdog unit set after `daemon-reload`.
- The focused source regression suite passed 4/4.
- The owner service, owner-heartbeat service/timer and watchdog service/timer
  all remained disabled and inactive.
- The whole-host lease remained `ready`; no lease, lock, operation lock,
  evaluation identity or evaluation lease state was created.
- The October 26 F2 prepare and final timers remained enabled and active for
  01:15 and 01:20 PDT respectively.

The first remote transaction invocation returned success without changing the
target. An immediate independent hash and checkpoint read caught the no-op.
The same approved transaction was then executed from a separately staged
script, after which the independent checks above passed. No partial change or
runtime effect occurred during the first invocation.

## Boundary

This closes only the missing systemd ordering edge. It does not arm F6, start
an owner or watchdog, create an identity, acquire a lease, stop a consumer,
run candidate H or M3, invoke recovery, call a model, or change F2/F3.
