# Stream A — B60 production-runtime reconciliation, 2026-10-11

**Scope:** read-only current-state check for Stream A's local-capability baseline.
This record does not evaluate SYCL performance, approve a model change, deploy
code or change any Decision Plane or authority gate.

## Verified current state

Direct read-only Proxmox/LXC checks found:

- The B60 at PCI `04:00.0` now has a **32 GB physical BAR2**. Its virtual
  resizable BAR2 still reports 256 MB. The earlier 256 MB *physical* BAR
  blocker in the dated B60 project baseline no longer describes this host.
- LXC 110 `aster-llama.service` is active/running with zero recorded restarts;
  its `/health` endpoint returned `{"status":"ok"}`. The running command is
  `llama-server` from `/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/`.
  The unit selects Level Zero GPU, SYCL fusion and the self-contained Intel
  loader/driver/oneAPI libraries. It serves Qwen3.5-9B Q4_K_M with a request
  for full layer offload (`-ngl 999`), one 8,192-token slot, flash attention, Q4 K/V cache and reasoning
  disabled at the same private address and port as before.
- The systemd unit uses `--api-key-file /etc/aster-llama-api-keys`; metadata
  shows the file is owned by `ollama:ollama` with mode `0600`. Its contents
  were not read. The separate environment file remains referenced by the
  unit; its contents were not read.
- LXC 104 `aster-agent.service` is active/running with zero recorded
  restarts. No authenticated generation or current quality/latency benchmark
  was performed by Stream A in this check.

The unit and process path identify the current serving build as b11429 SYCL
FP16. This is not a claim that all historical Vulkan benchmark results carry
over. The self-contained Intel libraries explain why a package-manager query
for `libze-intel-gpu1` and oneAPI runtime packages returned no installed
package names; it does not imply that Level Zero is absent from the running
service.

## Stream A consequence

Keep the same logical `local_model` capability and private endpoint contract,
but version its observed implementation as **Qwen3.5-9B Q4_K_M / llama.cpp
b11429 SYCL FP16 / B60 physical BAR2 32 GB**. Do not pool routing latency,
cost or failure measurements with the former Vulkan implementation without
recording the backend. D3 subscription-backed Codex handoff and M1 AI-PAM
authority gates remain independent of this backend switch. The closed local
general-sysadmin decision is not reopened by a faster or different kernel.

The operator reference's earlier Vulkan and small-BAR statements are historical
where labelled; its active runtime summary is updated separately. The B60
inference-engineering project still owns detailed backend acceptance, thermal,
stability and rollback evidence. Stream A must wait for that evidence before
claiming an efficiency or reliability improvement.

The repository gateway prompt was still telling Aster that Vulkan was active;
the hardware inventory and Second-Brain reference also stated the former BAR
block as current. The local prompt now requires current-operational evidence
for model/backend identity instead of hard-coding either one. Local reference
corrections reflect the live check. **The gateway correction has not been
deployed**, so the running Aster may still repeat the stale claim. The prior
sysadmin graduation and generalization suites are retained unchanged as
historical evaluation records.
Dated current-runtime copies update the model/backend expectations, the B60
diagnosis prompt and the time-sensitive Doctor question; the default evaluator
points to the dated graduation copy and requests `aster-qwen3.5-9b`. The copies
are regression candidates, not independently reviewed holdouts or evidence of
current model quality. Historical scores cannot be compared to these revised
labels as if the corpus were unchanged.

The separate curated `homelab-reference` repository also had 27B/Vulkan and
256 MB physical BAR claims under `current-operational` and
`current-with-exclusions` labels. Those three relevant source files were
corrected in local commit `9099718`; its unrelated pre-existing untracked
`.DS_Store` was left untouched. The deployed knowledge snapshot still contains
the former 27B/Vulkan Aster Operations page (read-only line check), and no
snapshot refresh has occurred. Correcting Git files alone does not repair
answers from the live snapshot.

An offline, clean-Git base-only snapshot from local commits `c739102` and
`9099718` passed the builder's source-content and provenance checks. It has 29
allowlisted sources, including the corrected operations and hardware records.
The deployed snapshot has 1,825 sources and includes the accepted derived
mirror. **The 29-source candidate must not be deployed**: a swap would remove
1,796 derived entries. The accepted mirror exists on LXC 113; a private,
read-only local copy was checked for safe archive members, all 1,796 entries
and generation hash `bf0c002f46a7aaffadadc2490045aaa9927cc091ea04eead2f413860e97491e8`.
That hash matches the deployed snapshot's mirror provenance. A complete
1,825-source candidate built twice from this input and the clean Git commits;
both archives had SHA-256
`a4a6e40040ca7dabe70a0e41525f84769f25b3500b2895c130c5002dad914987`.
All repository provenance flags are clean and the corrected operations source
is present. At this preflight stage the candidate remained only in
`/private/tmp`; the later bounded promotion is recorded below.

The candidate gateway was staged separately under `/tmp` in LXC 104 and tested
with its existing Python environment, without replacing or restarting the
running service. The first full run exposed one real fixture failure: a Doctor
incident test fixed its report timestamp to 2026-09-28, which the new
freshness guard correctly rejects. The fixture now uses the current test time.
After staging the repository scripts and ARR broker needed by the suite,
**197 gateway tests passed** in 4.858 seconds. This validates the offline
candidate, including the backend-neutral prompt and existing-reader hardening;
it does not prove deployed source compatibility or an authenticated 9B answer.

The repository's read-only `check-aster-b60.sh` candidate now checks the
private inference `/health` endpoint in addition to `xe`, service state and
Vulkan visibility. This reduces a false-positive monitoring gap after the
backend change; it still cannot establish answer correctness or sustained
SYCL stability. `sh -n` passed, and the uninstalled candidate passed once when
run read-only over direct SSH on the Proxmox host. It has not been deployed.

## Bounded live correction and postcheck

Further read-only inspection found that deployed LXC 104 source was not the
same file as this branch: SHA-256
`4bad7c6e8cdf9e89a1cde25014ce2d8ed5808dd3666bbf5fd47cf64698ced2a4`,
with three live-only symbols (`ASTER_RUNTIME_IDENTITY`,
`runtime_identity_requested`, `deterministic_completion`) and live UI changes.
The deterministic identity branch bypasses retrieval for explicit runtime
questions and itself said Vulkan. Replacing the deployed file with the branch
candidate would have erased those live changes, so no whole-file replacement
was made.

With an exact source-hash precondition, two narrow production corrections were
applied to the deployed file: the deterministic identity wording and system
prompt no longer claim Vulkan, and the current-runtime retrieval ranking now
prefers the reviewed `reference/operations/ai-local-inference.md` heading over
generic mirror entries matching numeric guest IDs. The old default model alias
and browser label were also aligned to 9B/SYCL. The final deployed source
SHA-256 is
`d6b3e6544593c029fde0831987cb3585422e0534c605f6e08da52d00ffe9589d`.
Rollback copies remain at
`/opt/aster-agent/rollback-aster-agent-sycl-wording-20261011.py` (original)
and `/opt/aster-agent/rollback-aster-agent-before-retrieval-20261011.py`
(after the first wording correction). A copy of the deployed source with the
second patch passed a direct retrieval check against the staged full snapshot;
the repository candidate's 198-test suite passed. The running gateway was
restarted after each bounded source correction and returned healthy with zero
recorded restarts.

The full 1,825-source archive, with the same accepted mirror digest and clean
provenance, was then staged under LXC 104, each file hash validated, and
promoted by renaming the old directory to
`/var/lib/aster/knowledge.before-sycl-20261011` before moving the candidate
into place. The old directory is retained. Aster gateway was restarted once
more; `/health` returned OK, systemd reported active/running and zero recorded
restarts, the live provenance still contained 1,825 sources and the same
mirror digest, and the `aster` service account retrieved the reviewed current
9B/SYCL operations record first for a representative runtime question. No
inference model or service, credential, policy, tool grant, Companion mode or
Codex handoff was changed.

**Remaining source-drift gate:** the deployed deterministic identity shortcut
has now been represented in this branch and the staged repository suite passes
**199 tests**. Its runtime declaration is still manually versioned and should
eventually come from a verified registry or source-local descriptor. Deployed
UI styling still differs from this branch; the reader was reconciled and
deployed in the separate bounded step below. Do not deploy the branch gateway
file wholesale until all live-only differences are reconciled and tested.
Authenticated end-to-end model answers, sustained stability, performance and
Doctor's active-SYCL coverage remain unverified. The local corrected
graduation suites were not sent to the model in this operation.

## Unknown / requires verification

- Matched SYCL versus Vulkan request latency, prefill, decode, energy and
  sustained stability for this exact model and workload.
- End-to-end authenticated Aster-to-inference behavior after the backend
  switch, including any model/template/streaming differences.
- Whether the current B60 checks and Doctor assertions still validate the
  *active* SYCL path rather than only Vulkan device visibility.
- Whether all inference key custody and recovery documents have been updated
  for the active `--api-key-file` option. No key or environment content was read.
- Whether the remaining deployed UI styling and any other source differences
  should be adopted into the branch before a whole-file deployment.

The initial discovery and candidate tests used no GPU load, model question or
credential read. The later bounded gateway and knowledge deployments above
did restart `aster-agent.service`; they did not restart inference.

The existing Aster Doctor reader hardening was then reconciled separately.
Transplanting the candidate function into a temporary copy of the deployed
source initially exposed two missing live imports (`stat`, `timedelta`);
after adding only those imports, the **hybrid deployed-source suite passed 199
tests**, and the current sanitized Doctor report returned its bounded `failed`
status with 32 checks. With an exact SHA-256 gate and a third retained source
checkpoint at
`/opt/aster-agent/rollback-aster-agent-before-doctor-reader-20261011.py`,
the function and imports were promoted. The final deployed source SHA-256 is
`b4f29f40a460d1feef95bc623c20c3219f94ede0be06acc684fabfde2d844192`.
After restarting only `aster-agent.service`, `/health` returned OK, systemd
reported active/running with zero recorded restarts, and the `aster` account
could still read the current 32-check aggregate. This hardens Aster's existing
model-visible human-summary path; it does not connect the D4 Doctor incident
adapter to Codex or approve schema 2.
