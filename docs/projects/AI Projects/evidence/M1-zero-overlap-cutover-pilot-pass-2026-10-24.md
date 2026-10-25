# M1 independent approval ingress — supervised pilot pass

Date: 2026-10-24 PDT  
Result: **PASS, followed by exact rollback to the recorded baseline**

## Scope

The pilot temporarily routed only `/v1/companion/approvals` through a dedicated
`aster-approval` process on LXC104 port 9121. Chat, voice, OpenBao and every
other Aster route remained on port 9120. The independent broker and ingress
remained static, non-enabled units. No approval, grant, model request or tool
execution was created.

## Passed gates

- The old approval service stopped first and its socket was absent before the
  independent broker started. Both approval brokers never ran together.
- The independent runtime parent was exactly `0711 hlabroker:hlabroker`; it was
  traverse-only for non-owners. The authority-bearing socket was exactly
  `0660 hlabroker:aster-approval`.
- The AI-facing `aster` UID was denied at the new socket. Dedicated UID 1905
  connected and received a valid content-free `automation.status` result.
- The approval-only ingress ran as `aster-approval`, listened only on
  `192.168.70.10:9121`, and recorded zero restarts.
- The temporary OPNsense rule was limited to
  `192.168.50.23 -> 192.168.70.10:9121/TCP`, used the established rule's
  sequence `2199`, and carried traffic before the sequence-2200 management
  block. Direct and public unauthenticated session requests both returned 401.
- The existing signed-in browser Companion showed zero pending approvals and
  loaded the read-only AI-PAM state. It required a fresh passkey before making
  management changes, which is the intended Yellow-only posture while the
  independent verifier has no production passkey-ACR mapping.
- During a brief execution-broker stop, the independent approval broker,
  ingress and session endpoint remained available. The dedicated identity
  continued to receive a valid content-free broker status. The execution broker
  then restarted healthy with its socket restored.

## Rollback and state proof

Rollback removed the longer-prefix NPM location first, stopped both independent
units, restored the old approval service, removed the temporary OPNsense rule
and reloaded NPM and OPNsense.

Postchecks show:

- NPM host 18 has no approval location and passes `nginx -t`;
- the temporary firewall UUID is absent and the original 9120 rule remains;
- `aster-agent`, `homelab-broker` and `homelab-broker-approval` are active;
- both independent units are inactive and static;
- the old approval and execution sockets exist, the new socket does not;
- port 9120 listens, port 9121 does not, and public Aster health is HTTP 200;
- a new consistent SQLite backup is byte-for-byte identical to the pre-pilot
  checkpoint at SHA-256
  `8c5da28339d15f87d62f2960f852f0f5d0aa7cef51971379ad45c4c8b183fd85`;
  database integrity is `ok`, with zero pending and zero approved-unconsumed
  requests.

## What this proves and what remains

This proves the zero-overlap identity boundary, routed token enforcement,
content-free Companion read behavior and independence from the execution
broker. It also proves restrictive rollback.

It does not make the route permanent, enable either unit at boot, prove restart
ordering, map a production passkey claim, authorize Red/management mutations,
grant a connected tool or enable automatic routing. Permanent Yellow-only
cutover needs its own reviewed deployment and boot/recovery checks.
