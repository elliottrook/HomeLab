# M1/D4 fixed Doctor F6 workload proposal — 2026-10-25

Status: **PROPOSAL VALID; NOT ADMITTED**

Stream A now defines the fixed Doctor usefulness run as a distinct proposed F6
workload rather than silently inserting it into the two-workload candidate-H
then M3 sequence.

The machine-readable proposal SHA-256 is
`8227321d42e93653c325ace233871a13e1c35d2945fb6c885c0f2e2db048c250`.
Its validator SHA-256 is
`ecd70ab4d586755194f7309fec25960006e60666ffae4f70a9dea45aa10a1b57`.

The proposal binds:

- the exact LXC104 packet, entrypoint, fixture and profile;
- a future fixed non-login identity and inherited read-only credential
  descriptor;
- fresh F2–F5 prerequisites and a whole-host lease;
- at most eight model requests, 60 seconds per case and 600 seconds overall;
- a 900-second recovery reserve and one attempt with no retry;
- only the private attempt journal and raw capture as expected outputs; and
- exact accepted Qwen3.5-9B Q4_K_M/SYCL and schedule restoration.

The proposal explicitly remains `not-admitted`, requires a separate reviewed
plan, disables tools, grants no authority and enables no routing. Two focused
tests reject admission, request-count, retry, tool, sequence-reuse and recovery
drift. The fixed Doctor source suite now passes 41/41.

No platform code, live service, lease or model call changed. The platform owner
must deliberately implement and review this third workload after the current
candidate-H/M3 activation path is complete; the proposal cannot widen that
existing sequence by itself.

