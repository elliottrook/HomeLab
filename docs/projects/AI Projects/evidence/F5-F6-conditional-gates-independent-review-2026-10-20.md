# F5/F6 conditional gates — independent review, 2026-10-20

## Result

Stream A independently reviewed platform commit `5106efc0` from an isolated
archive. Its focused pin/contract suite passed 2/2. The corrected card digest
is `29d8f292b987513e24e2364afb36ea004359a16d2b7bf8a848eb5e29f52f2d35`.

Two initially reported discrepancies were resolved by live read-only evidence:

- the accepted model path is a root-owned symlink, whose `0777` symlink mode
  does not make the target writable; it resolves through controlled parents to
  the pinned `ollama:ollama` mode-`0644` blob, and llama runs as `ollama`; and
- the fixed production observer namespaces are LXC104 `aster-agent.service`,
  LXC116 `aster-speech.service`, and LXC114's two News timers plus UI service.

The later F5 gate must observe these facts afresh; today's observation is not
future readiness evidence. F5 remains read-only and depends on successful F3
and fresh F4. F6 remains a separate approval to arm independent recovery, and
F7 human approval remains mandatory before a lease or service stop.

No permission, file mode, service, timer, receipt, lease, model, or host state
was changed by this review.
