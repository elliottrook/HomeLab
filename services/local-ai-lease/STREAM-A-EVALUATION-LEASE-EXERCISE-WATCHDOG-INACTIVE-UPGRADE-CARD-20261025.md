# Stream A exercise watchdog schema — inactive upgrade card

Status: **SOURCE-ONLY; ROLLED BACK AFTER VERIFIED TEST FAILURE; NOT AUTHORIZED**

This card replaces only the installed watchdog implementation so it can bind
the exact receipt-free exercise lease mode and two-minute/five-minute window.
It authorizes no identity, lease, recovery, consumer, model, timer, schedule
or remote Git operation.

## Exact one-file transaction

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/evaluation_lease_watchdog.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py` | `68f261c65f48443a7d7c2115ad0017a5de6f5866f9693143a53375e10d7a585f` | `19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53` | 0644 |

Source commit: `03abe317cb77d35ba4688b4220388b6f5abf3f4f`.

The required test-only follow-up is `046c6721eceeb30f30d28fa9703be2a5dcb07c0e`,
with `scripts/local-ai/test_evaluation_lease_adapter.py` SHA-256
`a51f7a8991508f369eea1b39cdd83e704f5267a38b66df55d2985622b0088f96`. It
corrects the nonblocking operation-guard race test so a losing outcome writer
retries after the competing heartbeat releases the guard.

## Required inactive sequence

1. Capture a root-owned checkpoint of the exact prehash, mode, owner,
   regular-file/no-symlink property and containing directory. Refuse on drift.
2. Replace only the listed watchdog file atomically, retaining root custody and
   mode `0644`. Do not change the owner/launcher packet, contract, adapter,
   entrypoint, wrappers, host exclusion, state, identity, units or timers.
3. Run the 46 evaluation-lease tests plus the 23 owner/watchdog/observer/
   launcher tests with Python `-B`; require all 69 tests to pass. Verify the
   watchdog accepts only the exact exercise mode/marker, lease/generation,
   two-minute hard deadline and five-minute restore deadline; healthy prepared
   state remains inert; owner loss/deadline recovery remains bounded and
   prepared recovery issues zero consumer commands.
4. Run imports, static hash/mode checks and `git diff --check`. Confirm all
   five F6 units/timers remain disabled/inactive and no runtime state exists.
   Do not invoke any watchdog effect path or live exercise.

## Failed attempt and rollback record

An inactive install attempt under approval was stopped when the required Linux
suite exposed a nondeterministic concurrency-test assumption: one isolated
rerun failed because the test required the nonblocking outcome writer to win
every lock race. The watchdog prehash
`68f261c65f48443a7d7c2115ad0017a5de6f5866f9693143a53375e10d7a585f` was
restored and reverified. No runtime state, unit activation, consumer command,
model call or schedule change occurred. After the test-only correction, the
full 69-test suite and 100/100 stress reruns pass locally.

## Rollback

If replacement or postcheck fails, atomically restore only the checkpointed
watchdog file, rehash it and verify root custody/mode. Preserve every other
packet and all runtime custody. If state is uncertain, retain the checkpoint
and stop for manual reconciliation; never retry automatically.

This card is a prerequisite for the prepare-only healthy-lease exercise. It
does not authorize that exercise or any effectful evaluation.
