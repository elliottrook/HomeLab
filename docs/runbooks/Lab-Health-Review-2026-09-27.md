# Aster, Doctor and configuration drift — 2026-09-27

Owner: Jason. Status: Doctor repaired; coordinated AI-PAM repair deployed under
Jason's subsequent **“Authorize full repair”** instruction; real iPhone acceptance
pending; drift reviewed, baseline not changed. The bounded Stream A repair and
current resume point are recorded in [repair evidence](../projects/AI%20Projects/evidence/M1-stage2-repair-2026-09-27.md).
Private Mac toolkit installation was separately approved through the platform prompt.

## Findings and recovery scope

The iPhone reaches authenticated Aster and can enqueue Doctor. The failed job
`0ac2836a9b0f4029b71e6c372e15ed69` encountered the same Doctor crash as the scheduled
08:15 report. Aster, its inference backend, speech ingress, notifications and lab
worker are running. This is not evidence of an iPhone connectivity outage.

Doctor's video-archiver parser expected legacy `event=error` records, while the
current archiver emits `event=file,status=failed`. Its summary reported one failure,
but the detail array remained empty. macOS Bash 3.2 with `set -u` aborted at that
array expansion, before producing the summary required by the job adapter.

Corrected the empty-array handling and support for both schemas, including current
`mode`, `considered` and `replaced` fields. Five regression tests pass; 18 worker
regressions pass. The full repository Doctor completes with **77 passed, 3 warnings,
2 failures**. Exit 1 now represents completed checks with real findings, not a crash.

Aster's pinned Doctor was from September 23 and also lacked the current NetBox SSO
redirect check, wiki quarantine check, thin-pool and configuration-backup checks.
Installed the current tested Doctor plus its missing `check-configuration-backups.py`
helper into the private toolkit after platform approval. No worker/service restart
was needed. Verified source hashes; rollback originals and manifest are at
`~/Library/Application Support/AsterLab/rollback-doctor-20260927T204514Z`.
The installed pinned copy also completed: **76 passed, 3 warnings, 2 failures**.
Its existing service inventory lacks the extra Paperless TCP row present in the
repository inventory; the dedicated Paperless health check still passes. No
service inventory was changed in this two-file repair.
Scheduled Doctor uses the repaired repository file. Existing failed job history
is retained; a new Companion Doctor request is required to prove queue-path recovery.

## AI-PAM approval inbox and management

**Update:** The mismatch described below has been repaired. Both entrypoints now
allow the verified owner; the matching restrictive approval daemon is installed.
A dedicated Authentik mapping proves WebAuthn from the token's own login event
and preserves original authentication time. Doctor now checks owner/assurance
configuration. Service, denial and offline tests pass; Jason's fresh iPhone login
and synthetic approve/deny/management acceptance remain necessary. No production
target action or general grant was added. The interim proposal below was not used.

### Original incident findings

Both views reject the user because the running Aster process has **no**
`ASTER_BROKER_APPROVER_SUBJECT_HASHES` configured. Its installed `broker_approvals.py`
has the newer explicit entitlement check. The approval daemon remains the older
September 24 version without its corresponding subject allowlist argument.
Both services are active. The live Aster/bridge files were modified September 26
at 12:45 PDT; this is a partial rollout/version mismatch. The precise deployment
command responsible has not been established.

The [M1 deployment plan](../projects/AI%20Projects/evidence/M1-deployment-plan.md)
and [Stage2 candidate](../projects/AI%20Projects/evidence/M1-stage2-candidate.md)
explicitly left this coordinated identity/assurance release undeployed. Live state
now contradicts that documented boundary. Do not restore the old permissive bridge
or label generic provider ACR/MFA as passkey proof to recover availability.

Source-local comparison confirms the configured lab owner matches **five consumed
approvals and two denials** in broker history. No owner hash, token, cookie or
credential is recorded here. There were zero pending/approved broker requests and
zero active lab jobs when checked. Exact source hashes and a bounded repair are
in the [candidate packet](../../ops/credential-broker/repairs/2026-09-27/README.md).
Ten gateway tests and ten new approval-service tests against copies of the live
core/transport pass. Full high-risk/management action recovery still requires the
Stage2 signed-session passkey assurance design and human login validation.

Proposed interim restoration: configure only the verified existing owner at both
entrypoints, install the matching restrictive approval daemon, and retain empty
passkey assurance allowlist. Inbox, management views, Yellow approve/deny recover;
Red approvals and management mutations remain blocked. This limited outcome needs
Jason's explicit decision before deployment. No Authentik, firewall, credential,
grant, core or gateway change is included. Capture protected checkpoint/SQLite
restore proof; restart only approval and Aster; fail closed on verification failure.

## All reported drift entries

Baseline accepted **2026-09-15 13:15 PDT**. Rebuilt the current manifest without
sending notifications or accepting a baseline: **25 entries (10 added, 15 changed)**.
The earlier conversational count of 24 was a counting error. Parent XML digests
repeat changes already represented by child entries; these are not 25 independent
incidents. No removed manifest entries.

Compared September 15 backups with September 27 06:00 backups. The current OPNsense
XML SHA-256 exactly matches its live `/conf/config.xml`; all 15 changed/added Proxmox
files exactly match live SHA-256 values. Arista's reviewed backup changes are the
recorded MacBook account addition and startup timestamp; current Doctor confirms
links, temperature, PSU and unchanged error counters. This is a configuration audit,
not an assertion that the drift manifest covers every installed application.

| Manifest entry / entries | Observed change | Disposition / evidence |
|---|---|---|
| `opnsense:wireless` | Empty element added | No wireless configuration enabled; serialization/migration artifact |
| LXC `115.conf` | Paperless at `.70.15`, 4 GiB | Expected completed Paperless deployment/IP correction; no collision with speech |
| LXC `116.conf` | Speech at `.70.14`, 4 GiB | Expected Companion speech deployment |
| LXC `117.conf` | OpenBao at `.50.24`, 2 GiB; retained recovery snapshot | Expected AI-PAM deployment |
| VM `118.conf` | S0 bootstrap fixture v0 | Expected retained stopped experiment |
| VM `119.conf` | S0 bootstrap fixture v1 | Expected retained stopped experiment |
| VM `120.conf` | S0 isolation fixture v1 | Expected retained stopped experiment |
| VM `121.conf` | S0 isolation fixture v2 | Expected retained stopped experiment |
| VM `122.conf` | S0 corpus fixture v1 | Expected retained stopped experiment |
| VM `123.conf` | S0 corpus fixture v2 | Expected retained stopped experiment |
| Arista running/startup configs (2) | `jason-macbook` admin account and SSH public key; startup timestamp | Explicitly authorized and verified in MacBook Administration Layer, September 24; old admin retained; credential contents withheld |
| `opnsense:OPNsense`, `opnsense:configuration` (2) | Aggregate hashes | Explained by child changes below |
| `opnsense:OPNsense/Firewall` | 26 added scoped rules, ARR port alias, schema defaults, `tcp` normalization | Companion, Paperless, AI-PAM and Authentik rollout; no rule removed; new rules use named private endpoints/admin alias, none on WAN |
| `opnsense:OPNsense/Gateways` | Stored WAN_DHCP monitoring via 1.1.1.1 | Recorded September 23 health remediation; dynamic gateway remains |
| `opnsense:OPNsense/Kea` | DHCP4/6 model versions and explicit subnet IDs 1/2 | Migration metadata/defaults; no subnet address change observed |
| `opnsense:OPNsense/unboundplus` | 24 private service DNS names pointing at NPM `.50.23` | Recorded private SSO/Companion service routes; seven prior entries retained |
| `opnsense:dnsmasq` | MacBook reservation MAC correction; explicit `expand_hosts=0` | Recorded MacBook access work; false default is migration noise |
| Proxmox `jobs.cfg` | Exclude generated news `latest.mp3` | Explicit September 16 request, archive verification documented in News Aggregator Audio Digest |
| LXC `101.conf` | RAM 4096 → 6144 MiB | Recorded/reconciled memory rebalance |
| LXC `106.conf` | RAM 4096 → 6144 MiB | Recorded/reconciled memory rebalance |
| LXC `108.conf` | RAM 2048 → 1024 MiB | Recorded/reconciled memory rebalance |
| LXC `110.conf` | RAM 10240 → 16384 MiB | Recorded/reconciled memory rebalance |
| Proxmox `user.cfg` | `jason@authentik`, propagated Administrator | Explicitly accepted SSO promotion; user comment still says read-only pilot and is stale metadata |

The six VMs have no vNIC, `onboot=0`, 1 GiB RAM/8 GiB disk each and are stopped.
Their accepted execution/retention records are on the active
`codex/aster-m2-reconcile-f25` worktree at `/private/tmp/aster-m2-reconcile-f25`,
commit `8fd5f8d4c58ca1bd600f47f5c4a2e60cc168b0b0`. Main's portfolio does not yet
include this newer evidence. Do not delete fixtures as drift cleanup.

Supporting records: [MacBook](../projects/MacBook-Administration-Layer.md),
[memory rebalance](../projects/archive/Aster-Personal-Assistant.md),
[WAN/migration work](Lab-Health-Remediation-2026-09-23.md),
[Authentik rollout](../projects/completed%20projects/Authentik-Rollout.md),
[news backup exclusion](../projects/completed%20projects/News-Aggregator-Audio-Digest.md),
[AI-PAM](../projects/homelab-credential-broker.md).

Recommend accepting these reviewed changes after Jason's decision, preserving the
old baseline and comparing a fresh manifest to the reviewed candidate before
acceptance. Do not accept intervening changes silently. The active baseline and
notification suppression state were not modified by this investigation.

## Real remaining findings

- Video archiver: 110 replacements, one failed output-size verification (2,084,858,762
  bytes exceeds its cap). The protection rejected the output; do not bypass it.
  Its separate Jellyfin rescan call returned HTTP 401. No key was read or rotated,
  no conversion or scan was retried. Review the source-local integration separately.
- Latest lab job is the historical crashed Doctor run. A new completed run should
  supersede it; do not erase the failure record.
- TrueNAS Media pool: 84% used. Capacity warning remains valid.
- Wiki collector: seven sources quarantined with `repository-ref-commit-mismatch`:
  Home Assistant, Jellyfin, OPNsense, Pi-hole, Proxmox, SABnzbd and TrueNAS docs.
  Upstream refs moved beyond accepted commits. Pinned-source review remains
  necessary; no quarantines or content pins were weakened.
- Working tree contains unrelated user work, preserved. Git warning is expected.
- AI-PAM live application files are outside the infrastructure drift manifest;
  this mismatch demonstrates a monitoring coverage gap. Add explicit entitlement/
  assurance readiness reporting in the coordinated repair, rather than relying
  on service-active checks alone.

The initial investigation made no remote writes. The subsequent authorized repair
changed only the scoped Aster/approval runtime and Companion claim mapping,
with protected restore-tested checkpoints. No Git push, baseline acceptance,
credential rotation, guest deletion or storage cleanup occurred.
