# D4 fixed Doctor response v2b cutover result — 2026-10-26

## Result

**PASS / LIVE.** The freshness-corrected fixed Doctor response candidate from
source commit `57487bc3` passed its approved caller-only cutover and an
independent live-socket canary.

The bounded canary established:

- `ok: true` and schema `2`;
- capability `diagnostic.aster-inference.latest`;
- source `homelab-doctor-structured/v2` and state `ok`;
- the observation age was within the source's 129,600-second bound;
- the deterministic answer was nonempty; and
- authority remained exactly `not-granted`.

No answer text or private report content was retained.

## Installed identity and recovery

- live caller SHA-256:
  `d1b567a8c7f0f205a6bd3fdc4d397ba03355f695995de74337fc4848e0cf9e48`;
- live response SHA-256:
  `4ca8721b1076815de3220dc51a1e499fd6822f3a9a1085bfc561804bea065298`;
- retained predecessor SHA-256:
  `aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a`;
- checkpoint directory: root-owned mode `0700`;
- checkpoint file: root-owned mode `0600`.

The fixed caller and gateway were active after cutover. Aster Agent and the
accepted SYCL inference service remained active with zero reported automatic
restarts, and Speech remained active. Only the fixed caller service was
restarted under the approved effect.

## Scope

This completes one useful deterministic read-only diagnostic presentation. It
does not grant a repair tool, generic Doctor access, automatic routing, model
promotion or broader authority. The rollback checkpoint is retained.

