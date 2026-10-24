# M1 zero-overlap cutover — static preflight

> Result: **STATIC GO — live supervised pilot still requires approval**
>
> Source/card commit: `da86ed53`

The approval-ingress branch was published to Forgejo and its GitHub mirror at
the same full commit `da86ed531d74acd69224b362c67d47075dfcc089` before this
preflight.

Read-only checks on LXC104 confirmed the four installed hashes, UID/GID and
environment metadata still match the inactive-install result. Both new units
remain inactive, non-enabled and never started. The current three production
services and port 9120 are healthy, port 9121 and the independent socket are
absent, and the current approval socket is present. The broker database has zero
pending and zero approved-unconsumed requests; no row or payload was read.

NPM host 18 passes `nginx -t`, retains `/voice/v2/` and `/voice/`, has its root
backend on `192.168.70.10:9120`, and has no approval custom location. The loaded
firewall contains the exact NPM-to-9120 rule and no NPM-to-9121 rule. These are
the expected pre-cutover conditions rather than missing implementation work.

The static pilot gate is therefore ready. Fresh checkpoint, host health and
operator-presence checks still run immediately before any live change. The live
pilot must add the exact 9121 path, enforce stop-old-before-start-new ordering,
obtain one content-free existing-session result, test execution-broker
independence, and then restore the current route under the same zero-overlap
sequence. It creates or consumes no approval and leaves no permanent route,
firewall or service enablement.
