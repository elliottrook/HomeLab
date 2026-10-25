# Stream A prepare-only recovery exercise — exact one-attempt card

Status: **SOURCE-ONLY; ONE ATTEMPT NOT AUTHORIZED OR RUN**

This is a fresh, exact one-attempt card after the guest-path and observer
repairs. It is valid only outside the October 26 F2 margin and never retries
automatically. The attempt ends before consumer quiescence and must be followed
by full post-attempt reconciliation.

## Installed custody pins

The runner must verify every host pin and both LXC110 guest pins before writing
any intent:

| Target | SHA-256 |
|---|---|
| evaluation contract | `5c5aa6c7174d53edb775f9a2640a867634b04a9b098d0742a589a1c2dc692686` |
| evaluation adapter | `6876e6892cae0d81c584fee7d6f3c5b79874d9b4737d250987f451f28b6aa910` |
| evaluation entrypoint | `0dab61905c834c36e3a865f8049c2650712422ddc27c534f1cd402b4e5ad52bb` |
| library watchdog | `19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53` |
| owner | `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1` |
| owner heartbeat | `4c45a07098eb8cca31bf95bb50b0824b65c6772e636627b23219761f359ed6cc` |
| effectful watchdog | `c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849` |
| restore observer | `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3` |
| lease wrapper | `15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af` |
| owner wrapper | `4d4e848eeafffdfa3aa9a0ba84097d94487318235442b1a4e4b8edc04a043014` |
| heartbeat wrapper | `e0162f60983601192c5f0fdd6d8395604e6636c05c9653c643d3722872dce12a` |
| watchdog wrapper | `65012c196134242a76a2131fbc9d7f28b50bcfd9137a87cfda0a416345430c99` |
| observer wrapper | `5cb6bec83864b5a8eeeb1b8c0624b93498fc04b2fcf36afb61e13caa0e64e8ab` |
| transient owner wrapper | `0d84d35300202c5d9316cc38a853402f7c252aab0ec5069f0b759dd3f3157d22` |
| exercise runner wrapper | `87f206b51bbe489a391ec43615644cc411cdc7cfe0666592fdb9ffe622ae300c` |
| LXC110 auth helper | `0996e1b565ad24b740997bbfe598065267e20380135a5af41687d0562239cae6` |
| LXC110 auth wrapper | `aac604de1f35c048791c5f1cfc21e25d9eb3e679fb7d799f74671307463313ac` |

## Exact bounded attempt

Preconditions must all pass or the attempt is a NO-GO:

- fresh read-only prestate passes; whole-host lease is `ready`, F6 units/timers
  are disabled/inactive, all four consumers are `enabled+active`, backend is
  authenticated/idle, and exactly one accepted GPU holder is present;
- the attempt starts at least 30 minutes before the October 26 F2 prepare
  timer and does not overlap either active F2 timer;
- all durable lease, lock, operation-lock, identity, intent, heartbeat, status
  and receipt paths are absent; exercise receipt directory is root-owned `0700`;
- the exact guest/helper and host custody pins above match.

The runner may then perform exactly once, in order:

1. Generate a unique `exercise-...` lease ID and owner ID; use generation `1`,
   marker `PRE-EFFECT-EXERCISE-NOT-PRODUCTION-EVIDENCE`, mode
   `stream-a-prepare-only-exercise-v1`, heartbeat timeout 5 seconds, a
   two-minute hard deadline and five-minute restore deadline.
2. Write only root-owned `0600` exercise and owner intents, then invoke
   `exercise-prepare`.
3. Start only the fixed transient owner, write one heartbeat, and run one
   healthy watchdog observation. Require `effects=not-attempted`.
4. Stop/collect only the transient owner, wait for bounded owner loss, and run
   one watchdog recovery. Require `effects=recovered` with nested
   `cancelled-prepared`; no consumer command is permitted.
5. Reconcile exact cleanup: lease, lease lock, operation lock, identity,
   heartbeat, status, restore intent and exercise intent absent; no receipt is
   written unless every final check passes.

No quiesce, post-quiescence, start, outcome, model call, completion request,
consumer systemd command, recurring timer arm, F2 mutation or automatic retry
is allowed. Any uncertainty retains evidence and stops.

## Post-attempt reconciliation

Regardless of success or failed-closed outcome, recheck F2 timer identities and
next runs, all F6 states, four consumers, backend/auth/idle/GPU observation,
whole-host lease, runtime paths and receipt custody. Record hashes/status only.
The prior approvals are consumed; this card itself does not authorize the
attempt.
