# D4 fixed Aster Speech — inactive installation result

**Date:** 2026-10-26  
**Frozen source:** `9a9263f3`  
**State:** installed inactive; activation not granted

## Result

The frozen nine-file fixed Speech bundle was installed additively in LXC104
after exact absence and dependency checks. The successful bounded installer
had SHA-256
`7971fba6224628ec98aa1300cde6acc67045a19413abc47459249a4653dca86d`.
The root-custodied rollback checkpoint is
`/var/lib/aster/fixed-speech-install-20261026-133133`.

An initial attempt correctly stopped before mutation because its absence check
did not accept systemd's normal `not-found` response. A subsequent transfer
used the wrong archive name and also changed nothing. The corrected attempt
completed, and independent postchecks verified:

- all nine installed files match the frozen manifest hashes;
- `aster-fixed-speech-caller.service` is disabled and inactive;
- `aster-fixed-speech-gateway.service` is disabled and inactive;
- both proposed sockets are absent;
- dedicated user `aster-speech-caller` has UID/GID 975;
- group `aster-speech-client` has GID 976 and contains only the intended
  existing `aster` member;
- the broker database has zero fixed Speech capability rows and zero grants;
- Aster Agent remains active with zero restarts; and
- transfer and staging paths were removed.

No broker source was replaced, no broker or Aster service was restarted, no
unit was started or enabled, and no diagnostic, model or repair action ran.

## Next gate

Reconcile and test an additive broker route for the distinct Green
`diagnostic.aster-speech.latest` capability. Activation later requires an exact
broker replacement/restart card, the single observer grant, starting only the
two dedicated fixed Speech units, and a bounded read-only canary. Those effects
are not authorized by this installation result.
