# M1 independent approval ingress — zero-overlap cutover card

> Status: **approval-ready for a supervised Yellow-only cutover; not authorized
> by this card**
>
> Installed candidate evidence:
> `M1-independent-ingress-inactive-install-result-2026-10-24.md`
>
> Target: LXC104 approval plane, NPM host 18 and one exact OPNsense rule

## Decision and user-visible effect

This cutover moves only `/v1/companion/approvals` from the AI-facing Aster
process on port 9120 to the dedicated `aster-approval` verifier on port 9121.
Both the Mac and browser Companion use that relative path, so the proxy change
covers both clients without rebuilding either application. Chat, voice,
OpenBao and every other Aster path remain on port 9120.

The first cutover is deliberately **Yellow-only**. The installed verifier has
no production passkey-ACR mapping. An entitled, signed-in owner may list, deny
and approve Yellow requests, while Red approvals and AI-PAM management changes
remain unavailable/fail closed. This is a deliberate operating tradeoff, not a
claim that generic MFA proves a passkey.

## Measured pre-cutover state

- The dedicated UID/GID, four pinned files and five-key configuration are
  installed and independently validated. Both new units have never run.
- The current approval service and Aster still use
  `/run/homelab-broker/approval.sock`; Aster remains an allowed peer there.
- NPM proxy host 18 sends `/voice/v2/` and `/voice/` to their existing speech
  backends and sends all other paths to `192.168.70.10:9120`. It has no approval
  location.
- The loaded firewall has one NPM `192.168.50.23` to Aster
  `192.168.70.10:9120/TCP` permit, UUID
  `1ae3b94b-18a5-4d5a-b19c-85b7b519c25c`, and no 9121 permit.
- The Mac client and browser source both call the exact relative prefix
  `/v1/companion/approvals`.

## Mandatory fresh gates

Abort before mutation if any installed hash, owner, mode or inactive-unit state
differs from the installation result; if LXC104/NPM/firewall health differs; if
there is a pending infrastructure maintenance operation; or if the existing
approval socket/database cannot be checkpointed. Count pending requests without
printing their payloads. The operator must have independent root SSH recovery.

Preserve before change:

1. a consistent broker database checkpoint and current socket/unit inventory;
2. an integrity-checked NPM database backup plus host 18's API/rendered record;
3. an OPNsense configuration backup and the exact existing 9120 rule; and
4. the current service, listener and Companion route health.

## Exact bounded change

1. Add one private firewall permit from only NPM `192.168.50.23` to only
   LXC104 `192.168.70.10:9121/TCP`, placed with the existing 9120 permit. Do not
   widen aliases or create Internet ingress.
2. Add one longer-prefix NPM host 18 location for
   `/v1/companion/approvals` to `http://192.168.70.10:9121` while preserving the
   suffix. Do not change `/voice/v2/`, `/voice/`, `/` or TLS.
3. With port 9121 still inactive, validate Nginx and reload NPM. Approval calls
   may fail closed during this bounded interval; chat/OpenBao must remain healthy.
4. Stop `homelab-broker-approval.service` and prove its old socket is absent.
   Do not start the new broker until that proof passes.
5. Start `homelab-broker-approval-independent.service`; require its new socket
   to be mode 0660, owned `hlabroker:aster-approval`, and reject a connection
   from UID `aster` before starting network ingress.
6. Start `aster-approval-ingress.service`; require only
   `192.168.70.10:9121`, exact unit identity/hardening and no restart loop.
7. Validate one existing Companion session against only the content-free
   `/session` response and one pending-count read. Do not print a bearer token,
   actor hash or request payload. Required result is entitled owner,
   `passkey_verified=false`, and a bounded pending count.
8. Stop the execution broker briefly and prove the new approval session endpoint
   and approval broker socket remain available, then restore the execution
   broker and verify its health. No approval is created or consumed.
9. Verify Aster chat, OpenBao status, speech paths, both Companion clients,
   broker database integrity, logs, listeners and NPM/firewall readback.

Do not enable either new unit until the supervised checks pass. If retained
after the pilot, add explicit enablement only as a separately recorded final
step after restart-order and recovery checks. No connected Codex tool or worker
grant is part of this cutover.

## Pass criteria

- there is no interval in which both old Aster and the dedicated verifier can
  reach an accepting approval socket;
- the routed approval path accepts only a valid entitled Companion token;
- missing, wrong, expired, wrong-audience and delegated tokens fail closed;
- Aster UID is denied at the new socket and dedicated UID 1905 is accepted;
- Red and management remain denied without a proven passkey mapping;
- the approval plane survives a bounded execution-broker stop;
- no approval or grant is created/consumed and the database remains consistent;
- chat, OpenBao and voice stay healthy; and
- human SSH recovery remains independent of Companion, NPM and Authentik.

## Restrictive rollback

On any uncertain result, first remove or disable the NPM approval location so
clients fail closed. Stop both new units and prove port 9121 and the new socket
are absent. Remove only the new 9121 firewall permit. Restore the old approval
service only if the separately approved run accepts returning temporarily to the
recorded pre-cutover Aster-trusted boundary; otherwise leave approvals unavailable
and use human SSH recovery. Never run both approval services together, restore an
older broker database over newer state, weaken token validation or invent a
passkey mapping.

## Exclusions and later work

This cutover does not grant a Codex worker, connect a diagnostic adapter, enable
automatic routing, change Authentik claims, consume an approval or authorize a
repair. A later passkey-claim experiment and exact mapping are required before
Red or management can move to the independent verifier.
