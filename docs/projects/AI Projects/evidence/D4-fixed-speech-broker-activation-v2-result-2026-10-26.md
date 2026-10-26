# D4 fixed Aster Speech — broker activation v2 result

**Date:** 2026-10-26  
**Packet:** `d4-fixed-speech-broker-v2`  
**Source:** `52ff3d64`  
**State:** complete; one read-only canary passed

## Result

The corrected v2 transaction completed once from the verified recovered
baseline. Its bounded socket wait removed the Type=simple readiness race and
the database remained under exact `hlabroker:hlabroker 0600` custody.

The one authorized canary returned:

- capability: `diagnostic.aster-speech.latest`;
- observation state: `ok`;
- authority: `not-granted`; and
- request status: consumed.

No model or repair path was called.

## Independent postchecks

- installed `broker_admin.py` SHA-256: `c04add38…bd765`, root:root `0700`;
- installed `broker_service.py` SHA-256: `b51df2bd…a5a3`, root:root `0644`;
- `broker_core.py` retained SHA-256 `2fdb8096…bf99`;
- broker database is `hlabroker:hlabroker 0600`;
- broker, Aster Agent, fixed inference gateway, fixed Speech gateway and fixed
  Speech caller are active;
- all four checked units have zero restart count;
- both fixed Speech units remain disabled for boot;
- the Speech observer is exact UID 975 in `observer` state;
- its service is the enabled proxy candidate;
- its only capability is Green, non-probation
  `diagnostic.aster-speech.latest`;
- its only grant is that capability;
- exactly one Speech request exists and is consumed;
- fixed inference retains its Green capability and sole grant;
- Forgejo read, safe-write, project-document and Lab Operations services remain
  enabled; and
- both Speech sockets exist while all transfer/staging paths are absent.

The root-only recovery checkpoint is
`/var/lib/homelab-broker/fixed-speech-pre-activation-20261026-r1`.

## Boundary after completion

This qualifies the second fixed observation class for normal bounded use. It
does not authorize repair, automatic routing, model calls, broader diagnostics
or boot enablement. The next D4 work is to integrate this fixed result into the
offline answer/selection boundary and evaluate usefulness without changing its
authority.
