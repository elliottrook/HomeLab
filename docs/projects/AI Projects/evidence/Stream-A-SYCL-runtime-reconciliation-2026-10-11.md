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

The repository's read-only `check-aster-b60.sh` candidate now checks the
private inference `/health` endpoint in addition to `xe`, service state and
Vulkan visibility. This reduces a false-positive monitoring gap after the
backend change; it still cannot establish answer correctness or sustained
SYCL stability. `sh -n` passed, and the uninstalled candidate passed once when
run read-only over direct SSH on the Proxmox host. It has not been deployed.

## Unknown / requires verification

- Matched SYCL versus Vulkan request latency, prefill, decode, energy and
  sustained stability for this exact model and workload.
- End-to-end authenticated Aster-to-inference behavior after the backend
  switch, including any model/template/streaming differences.
- Whether the current B60 checks and Doctor assertions still validate the
  *active* SYCL path rather than only Vulkan device visibility.
- Whether all inference key custody and recovery documents have been updated
  for the active `--api-key-file` option. No key or environment content was read.
- Whether the deployed gateway source and curated knowledge snapshot will be
  refreshed from these local corrections; neither was changed during this check.

No GPU load, model question, service restart, configuration write or credential
read occurred in this reconciliation.
