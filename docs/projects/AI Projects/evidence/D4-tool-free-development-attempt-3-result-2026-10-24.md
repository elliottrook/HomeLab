# D4 tool-free development attempt 3 — 2026-10-24

## Result

The explicitly approved run at digest
`9a089af8bf599bfbea35bc1ead7ea70d93c52f6345c7aeee2d40d77c118b2078`
completed all twelve reviewed synthetic sessions on the accepted Qwen3.5-9B
Q4_K_M / llama.cpp b11429 / SYCL service. It is a **contract NO-GO**, with
material progress beyond attempts 1 and 2.

- 12 sessions started and 12 finished.
- 32 model calls completed with `finish_reason=stop`; the 36-call ceiling was
  not reached and no retry ran.
- Ten sessions accepted two simulated checks and reached a third model call.
- One terminal `conclude` answer survived the engine boundary.
- Eleven sessions ended `invalid_terminal_check`: the model selected a terminal
  decision while leaving the advisory `check` string nonempty.
- Thirteen repeated observed citations were safely canonicalized. No
  unobserved citation or effect survived.
- Total recorded engine time was 106.850 seconds; per-session time was
  2.713–11.820 seconds.

The immutable owner-only journal remains at
`/root/aster-d4-development-evidence-20261024/attempt-3-ledger.jsonl` in
LXC104, mode 0600, SHA-256
`25941a8005f35b12bd3cbe7c41abe6d95b1c099b2064d71292e232f253a2df95`.
Temporary executable sources were removed after capture. The accepted service
remained active/running with zero restarts, Aster Agent and Speech stayed
active, and the lease returned `ready`.

## Measured correction

For a terminal `conclude` or `clarify` decision, `check` is unused and cannot
invoke a simulated or connected capability. Clearing that string is therefore
a syntactic canonicalization, not an authority expansion. The offline
candidate:

1. explicitly instructs the model to use an empty terminal check;
2. records whether a nonempty terminal check was cleared;
3. clears it before retaining the terminal answer; and
4. leaves actual `check` decisions subject to the existing capability,
   duplicate-use and two-check limits.

The complete evaluation suite passes 148/148. The next exact run digest is
`8f0cd102953d4b830e19b18bc4511bc2f9742356156d45d6f2fcbfee53d80c72`.
It needs separate approval; attempt 3's authorization is consumed.
