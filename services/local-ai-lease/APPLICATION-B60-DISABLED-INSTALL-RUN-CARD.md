# Application-only B60 controller/watchdog disabled-install card

Status: reviewable local candidate; not installed. This is a platform
installation gate only. It is separate from the 03:15 full-stop recovery drill
and does not authorize a lease, credentials, firewall changes, service starts,
consumer quiescence, or model calls.

## Exact scope

Install the corrected application-only controller and watchdog source on
Proxmox, install the systemd service and timer **disabled**, reload systemd,
and prove the candidate is inactive, has no lease state or lock, and cannot
start manually because the unit has `RefuseManualStart=yes`. The full-stop
units `local-ai-lease-watchdog.service/.timer` are out of scope and must not
be changed.

The candidate must use the corrected A1 sidecar pins:

| Artifact | SHA-256 |
|---|---|
| `application_b60_controller.py` | `e3100cccdcadf0327d26660e16a63913e4ff6c789a7a5f21339e98849ff15bcf` |
| `application_b60_watchdog.py` | `d8b11a849e875659f31d0383ce983897521d6bd0a19e36a9817a4737c7439a68` |
| `application_b60_lease.py` | `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d` |
| `application_b60_lease_recovery.py` | `3b855b60dfc9127c99c667bb8ccb7b198023b02f64e712877b5a7285416c0021` |
| `a1_ingress_policy.py` | `07be9c42650f74edbcb080d4b338bb01cc43a6ac18a847d86839c07a0ad65d1d` |
| `trusted_observer.py` | `fdc64fc200b87d0faba64a02762df3197fc49366dd0bec12b491ed83fb1aa93f` |
| `lease_watchdog.py` | `3146d292dd42a6a3f305b67cccf5518e7c0585c9c6de2e195d1a00686003d1fc` |
| `lease_contract.py` | `8a8997bdf453a499ae60dc2f11a65da9e28e318044a194122a7635b545adf113` |
| `application_receipt_boundary.py` | `147ba7fdfc6f46087cf77ca30060155dbe497a7d9a7c165f6b3f31f4d4f2a205` |
| `application-b60-watchdog.service` | `f7434db1f18afa4418f1217801152e35a2ae24388c20e04e47e3db8c3288cec7` |
| `application-b60-watchdog.timer` | `3e0be0830d60e586e53a1c3035abef7df802ecd156214ddc558f60677111d45a` |
| `application-b60-lease-recovery` | `309774dca1f0b5b37a9159b00fe6eed7b46f123f866c98e5d996e2c9fdc46499` |

The recovery source now matches the installed corrected A1 gateway and
isolated-app hashes (`b634b051…` and `e2e1150a…`); the former stale pins are
not acceptable. Its state has separate `restore_start_epoch` and
`restore_deadline_epoch` fields: the former begins the 15-minute reserve and
triggers restoration; the latter is the hard expiry and overdue condition.
The post-recovery observer must verify the exact accepted model, SYCL binary,
unit, GPU visibility, authenticated generation, all six schedule points, and
both restored consumer services before a lease can be released.

## Bounded install procedure

Only after an immediate approval for this card:

1. Record a root-owned preflight showing the current controller hash, whether
   each destination is absent, and that the full-stop watchdog units are not
   being modified.
2. Create `/usr/local/libexec/aster-a1` mode 0755 and
   `/var/lib/local-ai-lab/application-b60` mode 0700. Copy only the listed
   source files, wrapper, service, and timer with root ownership and mode 0644
   (wrapper mode 0755).
3. Run `systemd-analyze verify` on the two units and `systemctl daemon-reload`.
4. Run `systemctl disable application-b60-watchdog.timer
   application-b60-watchdog.service`; do not enable, start, unmask, or trigger
   either unit. Do not create `application-b60.json`, its lock, credentials,
   checkpoints, or receipts.
5. Record a content-free receipt containing only hashes, ownership, unit state,
   absent state/lock paths, and the unchanged full-stop unit identity.

## Expected observable state

```text
application-b60-watchdog.timer: disabled, inactive
application-b60-watchdog.service: disabled, inactive, no PID
/var/lib/local-ai-lab/application-b60/application-b60.json: absent
/var/lib/local-ai-lab/application-b60/application-b60.lock: absent
full-stop watchdog: unchanged
LXC104/LXC110/LXC116 services: unchanged
```

The install must abort before copying if a destination contains an unexpected
candidate, if any hash differs, if a full-stop unit changes, or if any service
is active as a consequence of the operation.

The disabled installation does not claim those runtime checks are live. The
platform must not request the later recovery-drill approval until the exact
observer closure above is installed and its source-bound probes have been
reviewed.

## Rollback

Disable the candidate timer/service, verify no candidate process and no lease
state exist, remove only the newly installed candidate files and empty state
directory, run `systemctl daemon-reload`, and restore the recorded preflight
hash/state. If any state file, lock, process, or ambiguous unit state exists,
do not delete it; retain it for reconciliation and stop for operator review.

## Explicit exclusions

This card does not authorize the 03:15 full-stop drill, the separate
application-only Stage 1/Stage 2 recovery drill, lease issuance, temporary
LXC110 key material, ingress/firewall changes, stopping or masking Aster/Speech
or News, starting the A1 sidecar, a backend request, a model call, backup
schedule changes, or Git push.

## Source-only gates that remain after installation

The Mini-side runner already requires an authenticated external
`assert_admitted(profile_sha256, endpoint)` callback before the batch and
before every call; it returns a content-free authenticated receipt containing
lease ID, generation, host receipt digest, profile hash and exact endpoint. It
binds the exact endpoint
`http://192.168.70.10:19104/v1/chat/completions`, rejects any result other than
an authenticated receipt, records the receipt provenance in the owner-only
`final-manifest.json`, and records no request content. The platform still must
supply that trusted callback and a source-bound same-night backup receipt
binding Proxmox, TrueNAS guest, LXC110, and Mac evidence to the selected lease.
Schedule metadata alone is not that receipt. These remain separate gates for
the later 20-call approval.
