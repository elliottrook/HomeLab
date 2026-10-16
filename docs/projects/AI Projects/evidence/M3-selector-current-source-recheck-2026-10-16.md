# M3 selector source recheck — 2026-10-16

**Evidence class:** offline synthetic conformance only. No route, model,
tool, network or production setting was changed.

The historical full-file-pinned v1 source definition expects SHA-256
`343bce00b777134bfb6f28f7e3218bea3a21240ed19f9cb0bad819186ab2deb0`
and still rejects this branch's current `aster_agent.py`. Its observed
full-file SHA-256 is now
`d6a05bcc7edddb1eaa69a67450cfc48c1c0e96ba8688de7a1246a1e9eb847e11`.
This is expected drift from the frozen historical experiment, not a reason
to repin or rewrite that result.

The separately reviewed v2 component-pinned selector probe accepted the
current source. It observed these source-component digests:

| Component | SHA-256 |
|---|---|
| `TOOLS` | `ec7eac78dfcee6f5277cf28c2b75b8d2f4bc1bc23143a2ea2248a9535f0ec0f0` |
| `TOOL_HINTS` | `c1bfb98811bd25c96a66a82f14c149252740d5b26c5b3cca15dc0c5af7d41215` |
| `select_tools` | `ce376620beb4958e7c7d7abe22489a2bb8af90e1d72cccfce7567a6f6a5dd82c` |

The offline run checked 12 existing synthetic fixture selections with 10
warm repeats each. The `test_conformance` and `test_contracts` suites passed
31/31 under bundled Python 3.12/Pydantic 2.13.5. The first attempted v1
contract test run in this session failed at the pre-existing full-file pin;
the exploratory contract edit was reverted completely before this v2 run.

This preserves the historical baseline and establishes only that the selected
v2 source components still match their reviewed definition. It does not
establish user-route correctness, calibrated abstention, local-model quality,
Codex comparability or automatic-routing authority. Those require an
independently labelled corpus and a separate shadow/evaluation decision.
