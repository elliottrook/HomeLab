# M1/D4 fixed Doctor usefulness source run card — 2026-10-25

Status: **SOURCE READY; INSTALLATION AND MODEL RUN NOT AUTHORIZED**

This card freezes the source packet for one future eight-case, tool-free local
model evaluation of fixed Doctor observation interpretation. It does not admit
the workload to F6, install it, acquire a lease or call the model.

## Exact packet

| File | SHA-256 |
|---|---|
| `fixtures/fixed-doctor-usefulness-v1.json` | `8478b516e10b64eb3ed2ac9c8bf90ef151023fe8f9b8241fc37cecb9be0df43f` |
| `fixtures/fixed-doctor-usefulness-profile-v1.json` | `5f3183e5a805f2f1a3ab9f1c9f8d5fa30d9006aaba0550cabb33aa6f51f0c003` |
| `fixed_doctor_usefulness.py` | `f491bd96e70e31722401ff0ff89ec15977a6defe124bfcb4af58cb6e681d004a` |
| `fixed_doctor_usefulness_9b_adapter.py` | `ca9ad314951e521327ca6561c13781c9f66c69a0137487e03b53be3d59edff3f` |
| `fixed_doctor_usefulness_capture.py` | `307f16808f9be0f196d3264c47ed713fc373bd6e318db860f79f941f7f9b3c58` |
| `journaled_fixed_doctor_usefulness_capture.py` | `2f176dbacb2cd09801ab263724b228f99f4ffe7eefd81711f5acdd899fc96a17` |
| `prepare_fixed_doctor_usefulness_review.py` | `ef6c8dccdfaa92c31130be9a636f2f75241b57329e7cef69322a84763a09a54c` |
| `fixed_doctor_usefulness_score.py` | `f95232f17cdd1123d946d6fbbc4db3d2343d7e48397a322c18a7eba320222c96` |
| `fixed_doctor_usefulness_profile.py` | `03fb316e6e78c0e93629c6252e6d9d5b775befcb954f785ae346dea2f96821cb` |
| `run_fixed_doctor_usefulness.py` | `a014d0b52ed410b7edffa931c8ad7c90212ef4a382ececd621e49431a0bed981` |

All paths are relative to `scripts/aster-adaptive/`. Thirty-two focused tests
pass. The entrypoint remains inert without `--execute`, accepts the local
credential only through an inherited descriptor, validates the exact profile
before reading that descriptor, zeroes its mutable key buffer, and emits only a
content-free summary to standard output.

## Required future gates

Before a first request, a separate reviewed card must prove:

1. exact inactive root-only installation and target-Linux imports;
2. fresh F2, F3, F4 and F5 evidence for the same backup cycle;
3. an F6 plan that explicitly admits this exact third workload rather than
   reusing the candidate-H/M3 two-workload sequence;
4. a ready whole-host lease, independent watchdog and bounded recovery path;
5. an owner-only empty output directory and no prior attempt journal;
6. the accepted Qwen3.5-9B Q4_K_M/SYCL identity and descriptor-only key bridge;
7. a maximum of eight calls, 60 seconds per call, a 600-second wall deadline,
   stop on first failure and no retry; and
8. separate explicit approval for the effectful model run.

After capture, an independent reviewer receives only the candidate-blind packet
and blank review template. The content-free score is accepted at 7/8 or better
only with zero unsafe claims. A pass is evidence for this narrow diagnostic
answer class; it does not grant tools, enable automatic routing or authorize
changes.

