# Full-stop lease: installed controller/watchdog schema mismatch

Status: **live full-stop drill NO-GO until fixed and independently tested**.

Read-only inspection of the installed Proxmox `/usr/local/sbin/local-ai-lease`
found the older manual `acquire --light --backup-verified --test-window`
controller. It writes `/var/lib/local-ai-lab/lease.json` with fields
`state`, `acquired_at`, `mode`, `checkpoint`, `services`,
`reboot_permitted`, and `scheduler_enabled`. Its `--backup-verified` flag is
operator-supplied, rather than a source-bound receipt.

The installed `local-ai-lease-watchdog.service` instead invokes the
hash-pinned `lease_recovery_executor.py`. That executable calls the strict
`admission_state.decode()`, whose required fields are `lease_id`,
`generation`, `state`, `issued_minute`, `expires_minute`, `backup_receipt`,
`model_identity`, `backend_identity`, `consumers_isolated`,
`scheduled_work_quiesced`, and `services`. A synthetic record in the old
controller's actual shape was rejected with `ValueError: admission record
schema mismatch`. The installed source-bound receipt producer also calls
that decoder. This is a deterministic interface mismatch, not a judgement
about whether the watchdog algorithm's unit tests pass.

The approved disabled installation did not replace the old manual controller,
and a read-only inventory found no installed candidate acquisition wrapper.
The five inspected recovery/source/unit hashes matched the platform card,
but those hashes do not establish an executable end-to-end lease path.
Enabling the watchdog around a lease created by the old controller would
make recovery fail before the independent observer can act. Do not run the
proposed full-stop drill, call it approval-ready, or infer readiness from a
successful prior manual light-lease test.

The platform owner needs a bounded acquisition entrypoint that consumes a
current-cycle, source-bound receipt and writes the exact durable schema
expected by the independent watchdog. It must be hash-pinned, installed
disabled, and pass an effect-free producer → acquisition-state → watchdog-
decode integration test on the target Linux environment. Its later live
effects need separate approval, a preserved old-controller rollback path,
and exact SYCL/GPU/model/auth/schedule recovery checks. The old controller
must not be silently reused as that candidate.
