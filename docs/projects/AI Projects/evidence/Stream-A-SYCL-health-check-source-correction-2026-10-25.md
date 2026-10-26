# Stream A SYCL health-check source correction — 2026-10-25

Status: **SOURCE AND LIVE READ-ONLY CHECK PASS**

The shared `scripts/check-aster-b60.sh` still treated the retired Vulkan/27B
path as production even though the accepted service is llama.cpp b11429 with
SYCL/Level Zero and Qwen3.5-9B Q4_K_M. That stale check could falsely approve a
rollback runtime or fail to verify the production backend used by Stream A.

The corrected source now requires:

- host B60 `xe` binding and no persistent mapping in stopped rollback VM 105;
- running LXC104 and LXC110 with active Aster Agent and llama services;
- LXC110 `renderD128` with the expected render-group custody;
- active/running `aster-llama.service` with zero restarts;
- `ONEAPI_DEVICE_SELECTOR=level_zero:gpu`;
- the accepted `/opt/aster-sycl-b11429/.../llama-server` binary;
- the accepted Qwen3.5-9B Q4_K_M model and API-key-file boundary; and
- a successful content-free `/health` response.

A fixture-driven test rejects any Vulkan invocation and passed locally. Shell
syntax validation passed. The corrected script was then streamed to the
Proxmox host over read-only SSH without installation; it passed against the
live system. No file, unit, model, lease, timer or service was changed.
