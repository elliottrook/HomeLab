# M1 independent approval plane — permanent Yellow-only cutover card

> Status: **approval-ready; not authorized by this card**
>
> Prerequisite: the [supervised reversible pilot passed](M1-zero-overlap-cutover-pilot-pass-2026-10-24.md).

## Resulting behavior

Only `/v1/companion/approvals` moves permanently from Aster on port 9120 to the
dedicated `aster-approval` verifier on port 9121. Browser and Mac Companion use
the same relative path. Chat, voice, OpenBao and all other Aster routes stay on
9120.

The first release remains **Yellow-only**. An entitled signed-in owner may read
AI-PAM state, deny requests and approve Yellow requests. Red approvals and all
management mutations continue to require a proven passkey-specific claim, and
the independent verifier's passkey mapping remains empty. The UI therefore
continues to say that a new passkey sign-in is required before management
changes.

## Pinned release units

| Source | Target | SHA-256 |
|---|---|---|
| `services/aster-agent/delegation/deploy/homelab-broker-approval-independent.service.release` | `/etc/systemd/system/homelab-broker-approval-independent.service` | `348cea9bc22b1fd7cc5a978d9d8dd99355fee57b845d53046f6e0f742eaffbd6` |
| `services/aster-agent/delegation/deploy/aster-approval-ingress.service.release` | `/etc/systemd/system/aster-approval-ingress.service` | `53fb080b087e5caf694d8a363ec2561838730dd8e3e74bfbc2e355028c973c77` |

Both files pass 11 focused tests and target-Linux `systemd-analyze verify`.
The broker unit conflicts with the old AI-facing approval service, owns its
separate runtime path, starts before ingress and is enabled at
`multi-user.target`. Ingress requires the independent broker and is also
enabled at `multi-user.target`. Neither unit couples to the execution broker.

## Fresh preconditions and checkpoints

Abort before mutation unless:

- the installed modules, environment file and current static unit hashes match
  the pilot evidence;
- the old approval service, Aster and execution broker are healthy;
- port 9120 and both old sockets are present, while port 9121 and the new socket
  are absent;
- pending and approved-unconsumed request counts are both zero;
- NPM host 18 and OPNsense have no approval-specific route or rule;
- no backup, maintenance or lab lease conflicts; and
- independent PVE and OPNsense SSH recovery works.

Create fresh owner-only checkpoints of the broker database, both installed unit
files, NPM database and host-18 configuration, and OPNsense configuration. Test
the database and NPM backups before changing anything.

## Exact change

1. Install only the two pinned release units and run `daemon-reload`; do not
   start them yet.
2. Add the exact firewall permit
   `192.168.50.23 -> 192.168.70.10:9121/TCP` immediately after the established
   9120 rule, with sequence `2199`, then reload and read it back. The sequence-
   2200 management RFC1918 block stays unchanged.
3. Add only NPM host 18's longer location
   `/v1/companion/approvals -> http://192.168.70.10:9121`, preserve the suffix,
   pass `nginx -t`, and reload. All other locations and TLS stay unchanged.
4. Stop and disable `homelab-broker-approval.service`; prove the old socket is
   absent. Start the independent broker and repeat the live UID/socket checks
   before starting ingress.
5. Start ingress. Require exact identity, bind address, zero restart count,
   unauthenticated 401, authenticated entitled session with
   `passkey_verified=false`, zero pending requests and read-only AI-PAM state.
6. Enable both independent units only after those checks pass. Prove the old
   service is disabled and cannot overlap because of the new broker's
   `Conflicts=` relationship.

## Restart and recovery proof

After the live route passes:

1. restart the independent approval broker and prove the socket, dedicated-UID
   access and authenticated read recover;
2. restart ingress and prove public 401 plus authenticated read recover;
3. stop the execution broker, prove approvals remain available, and restore it;
4. reboot only LXC104 once from the PVE console and require all ordinary Aster
   functions plus the independent approval plane to recover automatically;
5. prove the old approval service stays disabled after boot, the two new units
   are enabled/active, both sockets and listeners have exact identities, and
   NPM/firewall state did not drift.

Expected Aster/AI-PAM interruption during the LXC reboot is a few minutes. B60,
speech LXC116, NPM, OPNsense, OpenBao itself and browser Companion files are not
rebooted or reconfigured beyond the exact route/rule above.

## Pass criteria

- zero overlap between old and independent approval brokers;
- Aster UID denied and dedicated UID accepted;
- valid entitled tokens accepted; missing, wrong, expired and delegated tokens
  denied; passkey false reflected accurately;
- Red and management fail closed; no request or grant created/consumed;
- approval reads survive an execution-broker outage and recover after both
  service restarts and the one LXC reboot;
- chat, OpenBao routes and voice remain healthy after recovery; and
- the post-cutover database is integral with unchanged bounded request counts.

## Restrictive rollback

On any failure, remove the NPM location first so the path fails closed. Disable
and stop both new units, prove port 9121 and the new socket absent, remove only
the 9121 firewall rule, restore the pinned pre-change unit files and run
`daemon-reload`. Re-enable and start the old approval service only after proving
the new broker is stopped. Never overwrite a newer database with the checkpoint;
use it only for comparison unless corruption is independently confirmed. Verify
9120 health, old sockets, NPM, firewall, counts and database integrity.

## Explicit exclusions

No passkey-claim mapping, Red approval, AI-PAM management mutation, connected
Codex tool, model call, automatic routing, B60 change, Authentik change, secret
read, OpenBao seal/unseal or browser/Mac application rebuild is included.
