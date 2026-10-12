# M3 selector-probe source-pin drift — 2026-10-11

**Decision: retain the historical experiment; do not silently repin or report a new routing score.**

The offline `services/aster-adaptive/evaluate.py` probe refused the current branch with `ValueError: baseline source changed`. Its frozen definition expects full-file SHA-256 `343bce00b777134bfb6f28f7e3218bea3a21240ed19f9cb0bad819186ab2deb0`, found at commit `29d04988038ea208e98ae4eec5e7d01bba102520`. The current branch file's SHA-256 is `93e689823913029c44c1a47e375c6c669004f436694a17e27cada3e6e7aaf140`. No output report was written and no router, model, tool or network call ran.

A read-only AST comparison of that pinned file and the current branch found identical `TOOLS`, `TOOL_HINTS` and `select_tools` nodes after excluding source-location attributes. Their respective AST SHA-256 values are `13e5dc2a3d86a1d06e6f2e4496abc468b004194ba5f45759776c3aec6be80343`, `cd065355ad1eb6742f33caf6af93e46f979bd6b2e9bb5b3b9a05b408a0e6de1f` and `1b73229b9915648d9a3bd825c96c400073acb55634e306352a7995aa3065f3f3`. Thus the branch's extracted selector and declared tool schemas appear structurally unchanged despite unrelated Aster source edits. This does not prove the deployed source is identical, nor does it make the old full-file pin valid for a new run.

For the next offline selector comparison, create an explicit experiment revision with a reviewed component digest that binds all three AST nodes, the full current source digest as provenance, and a check that `select_tools` has no undeclared global dependencies. Fail closed if any component changes or the source cannot be parsed exactly once. Keep the historical full-file-pinned result immutable. A new representative, independently reviewed corpus is still needed before any calibration, confidence threshold or production routing claim. No new framework or service is justified by this source-pin issue.

## Subsequent offline revision

An explicit `offline-experiment-definition.v2` candidate now pins the **source
segments** of the three extracted components, rather than Python's AST dump.
The first AST-dump attempt failed across Python 3.9/3.12 despite identical
source, so that candidate was corrected before acceptance. The source-segment
digests match both the old reviewed commit and current branch under both local
parsers. The historical v1 definition remains untouched and still rejects the
current full file. The v2 adapter records both its component pins and the
measured full-source digest; it does not treat the latter as a trusted pin.

The [retained synthetic result](M3-selector-pin-v2-result-2026-10-11.json)
contains 12 fixture selections with 100 warm repeats each. The evaluator's
assertions matched all 12 expected baseline selections. Its observed p95
selector time was 17,542 ns and adapter-plus-contract time was 54,083 ns on
this Mac; these are local CPU microbenchmarks, not inference or user latency.
Thirty offline tests passed, including changed-selector, changed-tool-schema,
duplicate-declaration, unreviewed-global-dependency, unrelated-comment and
no-egress checks. Even explicitly repinning a selector that references a new
global is rejected. No accepted
human-labelled corpus, model, live service or tool executed.

The v2 pin describes the **extracted offline selector**, not all possible
runtime mutations to Aster's globals or the currently deployed file. A future
serving decision still requires a reviewed runtime source/contract boundary and
representative independent labels. This revision does not promote a router or
change the M3/M4 gate.
