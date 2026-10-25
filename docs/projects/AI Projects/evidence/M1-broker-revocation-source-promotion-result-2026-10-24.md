# M1 broker capability-revocation source promotion result

**Result: PASS — installed and verified on 2026-10-24.**

Jason approved the exact two-module promotion described by the
[reviewed card](M1-broker-revocation-source-promotion-card-2026-10-24.md).
The installed files now match repository commit `c1d0eb38`:

| Production file | Installed SHA-256 |
|---|---|
| `/opt/homelab-broker/broker_core.py` | `2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99` |
| `/opt/homelab-broker/broker_approval_service.py` | `4a9f8d0de622a06e7dd9fe32279b22d71a3dbe4f220a77891684c34e30756631` |

Both predecessor modules and a consistent database checkpoint are retained
owner-only under `/root/aster-m1-broker-promotion-20261024` in LXC104. The
independent approval broker was restarted first and the execution broker
second. Both remained active with `NRestarts=0`.

## Boundary and recovery checks

- `/run/homelab-broker-approval` remained `0711 hlabroker:hlabroker` and its
  socket remained `0660 hlabroker:aster-approval`.
- Ordinary Aster was denied by socket permissions; the dedicated
  `aster-approval` UID connected and received the bounded automation status.
- Direct and public unauthenticated approval-session requests returned 401.
- The signed-in Companion read view recovered with no active request and still
  required a fresh passkey before any change.
- The execution socket remained `0660 hlabroker:hlabroker-clients`; Aster,
  ingress and both broker services were active, and Aster health returned 200.
- Thirty-four broker core/approval tests and six target-Linux HTTP/socket tests
  passed. They cover duplicate-consumer exclusion, stale policy, demotion,
  capability revocation, expiry, wrong-peer denial and Red fresh-passkey
  rejection using temporary databases only.

The first retained UID probe was accidentally invoked as a shell program even
though the helper has no shebang. It failed before contacting the socket; the
same pinned helper was immediately rerun explicitly with Python and produced
the expected two bounded results above. This was a test-command error, not a
service or candidate failure.

## Database invariant

The owner-only pre- and post-install consistent database checkpoints are
byte-for-byte identical, each with SHA-256
`8c5da28339d15f87d62f2960f852f0f5d0aa7cef51971379ad45c4c8b183fd85`.
Integrity is `ok`; all seven table counts are unchanged; requests remain 30
consumed, three denied, ten expired and four revoked, with zero pending and
zero approved-unconsumed requests.

No capability was revoked, granted or exercised. No production request,
passkey mapping, Red approval, browser mutation, model call, connected tool,
NPM/firewall/OpenBao or B60 change occurred. Production now contains the
tested capability-revocation method, but exposing or exercising that method
remains a separate gated operation.
