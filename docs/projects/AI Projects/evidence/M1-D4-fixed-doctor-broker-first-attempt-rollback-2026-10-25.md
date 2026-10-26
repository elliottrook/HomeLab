# M1/D4 fixed Doctor broker reconciliation — first attempt and rollback

**Date:** 2026-10-25
**Decision:** NO-GO; rollback recovered production; corrected retry required

Jason approved the exact two-file broker replacement and one controlled
restart from Stream A commit `5ad9cbc5`. Preflight matched both live source
predecessors, `broker_core.py`, source custody, active broker/Aster services,
zero fixed-Doctor database rows and the existing Forgejo project-document
capability tuple.

The staged candidates passed their target Python 3.13 compilation and exact
hash checks. The two sources were replaced and the broker restarted. The
postcheck then failed before enrollment or any fixed request because it tried
the ordinary health RPC as Unix user `aster`. That user is not a member of the
broker-client group and could not open the mode-`0660` socket. The registered
ordinary client is `hlabagent` (UID 995), a member of `hlabroker-clients`.

The automatic rollback restored both predecessor source hashes and the
database checkpoint. Its first recovery restart then failed because the
rollback installed the SQLite file as root:root instead of its measured
`hlabroker:hlabroker` custody. Under the already approved rollback obligation,
the database was returned to `hlabroker:hlabroker` mode `0600`, the failed state
was reset and only `homelab-broker.service` was restarted.

Recovery is complete:

- original broker source hashes and `broker_core.py` invariant match;
- broker and Aster Agent are active; broker `NRestarts=0` after recovery;
- the socket is `hlabroker:hlabroker-clients` mode `0660`;
- `hlabagent` completed the content-free health RPC;
- SQLite `integrity_check` returns `ok`;
- all five fixed-Doctor row counts remain zero;
- both fixed services remain disabled/inactive and both sockets remain absent.

No enrollment, grant, fixed read, model call, Forgejo write, project-document
change, schedule change or F2/F6/B60 action occurred.

The corrected apply script is pinned separately. It preflights the live
database/socket custody and `hlabagent` health call before replacement, repeats
that health check afterward, and restores SQLite as `hlabroker:hlabroker` mode
`0600` on any rollback. A new exact approval is required before retrying the
live replacement.

## Corrected retry result

The first corrected retry fixed the client identity and database rollback
custody, but returned NO-GO at the immediate post-restart health request. The
broker service was active and its socket path existed, yet the new listener had
not begun accepting connections; `hlabagent` received `ConnectionRefused`.
The corrected rollback restored the original two sources and database custody
without intervention. Subsequent read-only checks proved both services active,
broker `NRestarts=0`, the original source hashes, `hlabagent` health, SQLite
integrity `ok`, zero fixed rows and absent fixed sockets.

The next script replaces the socket-path readiness test with a bounded
successful `hlabagent` health-probe loop: up to 20 attempts at 0.5-second
intervals, with a two-second RPC timeout. It requires one successful health
response before continuing and repeats the same probe afterward. The script is
pinned at SHA-256
`fa28aad58a21a694c932c8e9ce698b0ce26fa3eb5b51804db0f18f0a27804a99`.
No enrollment, activation, fixed read or other excluded effect occurred.
