# Aster Lab Hours SA3 envelope r6 NO-GO — 2026-11-04

Booking `aster-stream-a-sa3-envelope-20261104-1500-r6` claimed exactly at
15:00:00 and ended at 15:03:10 after 190 seconds. It is spent and may not be
retried.

The terminal state is `no_go` at `owner-transaction`, failure code
`OWNER_TRANSACTION_FAILED_RESTORED`, with `production_restored=true`. No result
file exists. The bounded owner projection is:

`candidate-g guest exit-status:126;stdout-bytes:0;stderr-bytes:204`

Independent restoration found the lease ready, Doctor healthy with zero codes,
shared state/locks and port-11436 listener absent, dispatcher/Doctor/EPUB and
Proxmox services healthy, LXC104/110/116 running, Aster Agent, accepted
9B/SYCL llama and Speech active, and all three core restart counts zero.

The installed host adapter directly executed the LXC110 wrapper while that
root-owned regular file deliberately remained mode 0644. The wrapper has a
Python shebang but no execute bit; direct `pct exec` therefore returns status
126. A source correction now retains 0644 custody and invokes the exact wrapper
through `/usr/bin/python3 -B`. It passes the focused suite and a direct target
help-path proof without a listener, model call or effect.

R6 has no score and cannot advance to blind review. The correction requires a
reversible inactive installation and exact installed proof before any new
booking.
