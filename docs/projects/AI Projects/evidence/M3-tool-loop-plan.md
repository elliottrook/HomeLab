# M3 tool-loop comparison — frozen before execution

Synthetic manifest: `scripts/aster-adaptive/fixtures/tool-loop-v1.json`.
One and two sequential reads, invalid type/repaired call, malformed JSON/repaired
call, unknown tool and repeated invalid calls. Responses are fixed independently
of candidate output. Expected effects are literal fixture-call lists in the corpus.
No fixture success is a quality or real target-action claim.

Baseline executes the existing Aster `chat` function extracted from source, with
only its route decorator omitted. Lab Operations and initial payload preparation
are fixture stubs so the requested model-driven loop is exercised without preload.
The profile supplies both allowed fixture tools and caps Aster at four responses.
PydanticAI exposes the same two typed tools, with four response steps and bounded
validation retries. Both share a separate deterministic argument/authority boundary.

Record proposed calls, boundary attempts, accepted fixture calls, scripted response
steps, success/failure and latency. Both must execute exactly the expected call
list; unknown or invalid calls may never become accepted actions. A framework
rejecting an argument before dispatch is distinguished from a boundary rejection;
both are safe only when no fixture action occurs. Capture all failed cases.

Run conformance first; ordinary successful one/two-read cases get ten warmups and
200 retained latency samples. Run two fresh-process repeats, one active case,
10-second case timeout, no network, no actual model requests. No performance
adoption threshold is inferred from this loop; its extra responses are explicit
and must not be combined with preload-profile results. Candidate usefulness must
be demonstrated as removal of custom work without weakening deterministic checks.
