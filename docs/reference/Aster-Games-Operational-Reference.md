# Aster Games operational reference

> Authority: current live state with the exclusions below
>
> Reviewed: 2026-11-07

Aster Games is a private server-side retro-library platform. RomM is the
catalogue and user-state authority. ROMarr owns verification, duplicate
quarantine, and canonical import. A narrow broker exposes a sanitized catalogue
shape and pending proposals only; it has no approval or execution route.

The production server infrastructure runs in unprivileged LXC 129 on the
production application network. Canonical media lives on a quota-bounded
TrueNAS dataset. ROMarr is its only application writer and RomM mounts it
read-only. Untrusted download staging is a separate storage boundary.

Human administration uses private TLS endpoints behind Authentik and the
reverse proxy. There is no public DNS or ingress. Direct application ports are
restricted to the proxy, and the broker has no host listener.

The normal safety state has ROMarr automatic import disabled and its Prowlarr
and SABnzbd entries disabled even though their bounded connection tests pass.
Device installation and proposal execution are absent. The AsterTV v4 client
gate remains closed until AsterTV v3 has durable deployment evidence, clean
fleet evidence, explicit owner acceptance, and a separate approval to begin v4
client work.

Only lawfully usable material may enter staging. A completed download is not
trusted until it passes reviewed DAT classification, ambiguity rejection, and
duplicate handling. Monitoring must never expose catalogue titles, filenames,
save data, account data, credentials, download locations, or paths below the
approved storage roots.

HomeLab Doctor reports only component health, dependency state, storage
headroom, backup/recovery freshness, and the disabled safety policy. Beszel
provides host resource history. A healthy result includes acquisition and
automatic import disabled and the v4 client gate closed.

Recovery has three layers: the protected guest archive, daily retained media
snapshots, and a root-only application backup with a consistent database dump,
application/broker state, pinned runtime identities, checksums, and secret
references rather than values. The accepted isolated restore used a private
no-egress runtime, matched aggregate state and sampled-media integrity, refused
overwrite, detected capacity/dependency/authentication failures, recovered
after restart, restored exact pre-upgrade state, retained content-silent
observability, and destroyed its disposable runtime.

This reference excludes catalogue contents, private filenames and paths,
accounts, credentials, exact secret locations, and operational commands. The
HomeLab runbook owns detailed maintenance and recovery procedure. NetBox and
live service state outrank this point-in-time reference for current placement
and health.
