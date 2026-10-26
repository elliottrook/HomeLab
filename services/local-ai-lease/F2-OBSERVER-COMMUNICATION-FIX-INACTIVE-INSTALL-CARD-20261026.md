# F2 observer communication fix — inactive install card

Status: **REVIEW CANDIDATE; HOST INSTALLATION REQUIRES SEPARATE APPROVAL**

This card replaces only the installed F2 scheduled coordinator whose real
systemd path used `subprocess.run` and then called the Popen-only
`communicate()` method. It does not run F2, install a timer, create a receipt,
start a lease, stop a service or call a model.

## Exact identities

| Item | SHA-256 / custody |
|---|---|
| Source commit | `d00073e542aaebc816ddee31ae3a94fa3caacf07` |
| Installed predecessor | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1`; `root:root 0644`, one regular link |
| Replacement coordinator | `6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193` |
| Regression test | `2a21d2427a7110227cd7bbef0d6dcc5aae6ff97432dc0c102ffb49df8fc2032a` |
| Target | `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` |
| Preserved terminal state | `/var/lib/local-ai-lab/f2-scheduled/2026-10-26.json`; SHA-256 `51e296ea56cdf37af4a991ee33d3eaac38efa7865fa5212c707b823ce7320de6`; `root:root 0600`, one regular link |

Both recurring F2 timers must be disabled and inactive before and after the
transaction. No date-specific F2 timer may exist.

## Bounded transaction

1. Re-read the source commit and both candidate hashes from a clean commit
   archive. Reject a dirty-working-tree source copy.
2. Re-read the target with `O_NOFOLLOW`-equivalent custody checks and require
   the exact predecessor hash, `root:root 0644`, regular type and one link.
3. Require the preserved October 26 state to match its exact hash and custody.
   Require no F2/`zstd` child, lease, lock, receipt, backup, pull or maintenance
   process. Confirm LXC104/110/116 and the production Aster, accepted
   llama.cpp/SYCL, Speech, News and Proxmox control services are healthy.
4. Create a new root-owned mode-0700 rollback directory under `/root` and copy
   the predecessor there as `root:root 0600`. Verify its hash before changing
   the target.
5. Stage the replacement in the target directory, verify its hash, then
   atomically replace only the coordinator as `root:root 0644`, one regular
   link. Do not copy the test into a production path.
6. Import the installed coordinator with Python bytecode disabled and assert
   that `final.__kwdefaults__["popen"] is None`. Run the exact regression test
   from a root-owned temporary test directory with `PYTHONPATH` bound to the
   installed directory. Require the focused coordinator suite to pass 15/15.
   The regression must verify that the default branch calls
   `subprocess.Popen`, returns a Popen-compatible object and retains
   `start_new_session=True`.
7. Run the broader target-Linux `test_f2*.py` suite from the same clean source
   archive. Require 50 passes and one expected skip out of 51 tests.
8. Re-read the installed hash/custody, unchanged October 26 state digest,
   absent scanner/lease/lock/receipt, disabled/inactive recurring timers and
   healthy production services. Remove only the temporary test directory.

## Rollback

On any mismatch or failed test, atomically restore the checkpointed predecessor
and verify its original hash and custody. Leave the October 26 state untouched,
keep all F2 timers disabled/inactive and repeat production postchecks. Preserve
the failed candidate and bounded diagnostics in the root-only checkpoint; do
not retry the spent cycle.

## Pass boundary

A pass proves only that the fixed coordinator is installed inactive and that
the real default launcher contract works on target Linux. A fresh date-specific
F2 card, independent review and separate activation approval are still required
before another timed attempt.
