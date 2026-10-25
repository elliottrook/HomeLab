# M1 independent approval plane — permanent Yellow-only cutover result

Date: 2026-10-24 PDT  
Result: **PASS**

## Change applied

The reviewed permanent cutover moved only
`/v1/companion/approvals` to the independent approval ingress on LXC104 port
9121. The ordinary Aster application, chat, OpenBao and voice routes remain on
port 9120 or their existing speech route.

The installed and boot-enabled units match the release card:

| Unit | Installed SHA-256 | Boot state |
|---|---|---|
| `homelab-broker-approval-independent.service` | `348cea9bc22b1fd7cc5a978d9d8dd99355fee57b845d53046f6e0f742eaffbd6` | enabled, active |
| `aster-approval-ingress.service` | `53fb080b087e5caf694d8a363ec2561838730dd8e3e74bfbc2e355028c973c77` | enabled, active |

The predecessor `homelab-broker-approval.service` is disabled and inactive.
Its socket is absent. The independent broker's `Conflicts=` relationship and
the observed stop-before-start sequence prevent overlap.

Nginx Proxy Manager host 18 now has one longer-prefix approval location to
`192.168.70.10:9121`. Its SQLite checkpoint passed integrity checking before
the change, `nginx -t` passed before reload and the location remained exact
after the LXC104 restart proof. OPNsense has the single permanent permit
`192.168.50.23 -> 192.168.70.10:9121/TCP`, UUID
`8b6d7185-7b33-4f4c-a8fb-a61c487170df`, adjacent to the established 9120 rule
at sequence 2199 and before the unchanged sequence-2200 management block.

## Identity and authorization proof

- `/run/homelab-broker-approval` is `0711 hlabroker:hlabroker`.
- Its authority-bearing socket is `0660 hlabroker:aster-approval`.
- The ordinary Aster UID is denied by the socket permissions.
- The dedicated `aster-approval` UID connects and receives a valid,
  content-free broker status.
- The ingress runs as `aster-approval`, listens only on
  `192.168.70.10:9121` and recorded zero restarts in the live pre-reboot tests.
- Direct and public unauthenticated session requests return HTTP 401.
- The existing signed-in browser session recovered the approval inbox and
  read-only AI-PAM view after each service restart and the container reboot.
  It reported no pending approvals and continued to require a new passkey
  sign-in for management changes. No management button was used.

This is the intended first release: Yellow review is available through the
independent plane; Red and management changes continue to fail closed because
no production passkey claim is mapped.

## Restart and independence proof

The independent broker restart restored its socket and both UID outcomes. The
ingress restart restored public 401 and the authenticated read path. While the
execution broker was stopped, the independent broker, ingress, dedicated-UID
status call and signed-in approval inbox all remained available. The execution
broker then restarted with its original socket and zero restart count.

One approved reboot of LXC104 completed successfully. After boot:

- `aster-agent`, the execution broker, the independent approval broker and the
  approval ingress were active;
- the old approval service remained disabled and inactive;
- ports 9120 and 9121 were owned by their expected Uvicorn processes;
- both Unix sockets had their expected identities and modes;
- NPM and OPNsense retained their exact route and rule;
- public Aster health was HTTP 200 and unauthenticated approval access was 401;
- the canonical voice health route was HTTP 200;
- the authenticated OpenBao route still required a session, while the
  source-local OpenBao health endpoint returned HTTP 200; and
- the signed-in AI-PAM view recovered with no active request.

## State and recovery evidence

The fresh owner-only SQLite checkpoint was integral before the change. It had
zero pending and zero approved-unconsumed requests and SHA-256
`8c5da28339d15f87d62f2960f852f0f5d0aa7cef51971379ad45c4c8b183fd85`.
A new consistent post-reboot backup is byte-for-byte identical, has the same
two zero counts and passes `PRAGMA integrity_check`.

The prior unit files, broker database checkpoint, NPM database and host-18
configuration, and OPNsense pre-change configuration remain under root-only
custody. No checkpoint was restored because all gates passed.

Two locally derived checkpoint helpers initially rejected their new nested
checkpoint paths before making a change. They were corrected to create the
owner-only parent chain and rerun successfully. A predecessor unit hash guard
also stopped before installation because it named the original inactive unit;
the live predecessor instead matched the later pilot-tested `0711` candidate
at `7452c086...`. The guard was narrowed to that reviewed predecessor before
the release units were installed. These fail-closed stops caused no service,
route, firewall or database mutation.

## Scope retained

No request or grant was created, approved, denied or consumed. No model was
called. No passkey mapping, Red authorization, AI-PAM management mutation,
automatic routing, connected tool, Authentik change, B60 change or OpenBao
seal/unseal action was introduced.

The next M1 work is offline boundary coverage for demotion, revocation,
expiry, stale request and duplicate-consumption behavior. Any live mutation
or real approval ceremony remains a separate gate.
