# A1 disabled-install card

Status: reviewable disabled-install request; **not deployed**. This card is
separate from the application lease, the 20-request benchmark, and the 03:15
full-stop recovery drill.

## Purpose and exact identity

This phase stages a test-only sidecar in LXC104 and proves its files and unit
are ready while keeping the unit disabled and inactive. It performs no model
call and does not claim an application lease.

| Item | Required value |
|---|---|
| Guest/unit | LXC104, `aster-a1-test.service` |
| Identity | dedicated UID/GID 1904, unprivileged, no supplementary groups |
| Listener | `192.168.70.10:19104`, no listener during this phase |
| Backend reference | `http://192.168.70.12:11435/v1`; no backend mutation |
| Mini peer pin | `192.168.1.206/32`, verified as the source seen by LXC104 |
| Profile | `a1-full-path-9b-candidate-profile-v1.json`, SHA-256 `af29955fb519aecfcfabeb741f7308fcf6f3c927cab647f8ab4396851846451e` |
| Source class | Stream A candidate-path baseline, not production Aster performance |

The systemd network boundary is symmetric and therefore permits only loopback,
backend `192.168.70.12/32`, and Mini `192.168.1.206/32` as peers. A later live
probe must independently validate the host/network ACL and both directions;
this card does not install or validate that ACL.

## Artifacts to stage

Copy only the reviewed source closure, the exact dependency wheelhouse, the
disabled unit, and owner-only empty data directories. Verify every digest
before considering the phase complete:

- `a1_isolated_app.py`: `b634b0518f018befc88f57697b55ad1ef1011fc107c1088bd90158656c53fed4`
- `a1_test_gateway.py`: `e2e1150a76fd6e61c47da1a6c6f3ce229905a454476c756c49d6a83c9d10aaae`
- `aster_asgi_clock.py`: `e7f8240fc38a62772ac2d7e4e9461ee8f3be21580885d9dfc0cab40fe1919305`
- `a1_headless_client.py`: `3d9c84735a7338860648215467996ff0f820aff8778acd7f7f42d6325dad6494`
- `a1_full_path_capture.py`: `a7bbb2b8fc98dd18c5d748a808e0e838b9c17dd80e84121e2d1e23ad006f9c86`
- `aster-a1-test.service`: `949bd266a68d9114034ab213208b0dafc6f7c77ef3e87b8225f314e949f59ac0`
- wheel manifest: `0fb7f44e2c856736ab741b23a70f28fa69dbd95a2eadad6c6d8d1b4416acadee`
- wheelhouse archive: `1a557fad83a896a52d675d21f8b00bb22cea74b641e73573d7af78d03da84765`

The wheelhouse contains 34 Linux CPython 3.13 x86_64 wheels. These SHA-256
values are integrity pins, not signatures. Installation must recheck the
archive, every wheel, versions, and imports on the target Linux guest.

The unit uses `LoadCredential=runtime.env:/etc/aster-a1-test/runtime.env` and
does not use `EnvironmentFile=`. No runtime credential file is created in this
phase; the unit must remain unable to start with missing test credentials.

## Explicitly allowed actions

1. Create only UID/GID 1904 and the sidecar directories under
   `/opt/aster-a1-test`, `/etc/aster-a1-test`, and `/var/lib/aster-a1-test`.
2. Copy the exact source closure and wheelhouse, with owner-only permissions
   and no credentials, production environment, OpenBao material, broker
   sockets, household knowledge, or Doctor state.
3. Install `aster-a1-test.service` and run target-Linux unit/hash/import
   validation while leaving it disabled.
4. Perform read-only checks proving `is-enabled=disabled`, `is-active=inactive`,
   no PID, no `19104` listener, no credential file, and no A1 evidence output.
5. Record a content-free staging receipt containing only digests, ownership,
   unit state, and validation results.

The later full-path phase must use a separately pinned Mini-side supervised
runner. Before any lease, it must read the sealed 20-case file, bind one
test-token input, revalidate the live host receipt before each call, forward
the bounded timeout, invoke the private capture path, and write a content-free
final manifest. Source-only functions are not a substitute for that runner;
its offline synthetic end-to-end fixture and hash must be added to the later
admission card before any protected window. The current reviewed runner is
`scripts/aster-adaptive/a1_admitted_batch.py`, SHA-256
`c87766ba4d514f87c0152f8dd64d8c6166ad9bf4987f4baaf31d91f64cb0687f`; its
offline fixture suite reports 31 focused tests. It is a Mini-side client only,
not a lease issuer or receipt verifier.

## Explicitly prohibited in this phase

No LXC110 key-file append or read-modifying checkpoint; no `aster-llama.service`
restart; no nftables or host ACL change; no service start/enable; no consumer
stop; no application lease or watchdog arm; no denial probe; no backend request;
no model call; no Mini capture; no production credential access; no Git push.

## Rollback

Because the unit must never start, rollback removes only the newly staged
sidecar files/directories and UID/GID after read-only checks prove no process,
open file, or `19104` listener exists. It does not touch LXC110, production
services, firewall state, leases, backups, or credentials. Any unexpected
running process or listener stops rollback and leaves the staging receipt for
reconciliation.

## Separate later approval

The application lease, temporary LXC110 test key, one controlled backend
restart, checkpointed ingress policy, host/network ACL proof, disposable
denial probes, consumer quiescence, recovery watchdog, and 20-request batch
require a new explicit approval against the full-path admission card. They are
not authorized by this disabled-install card.
