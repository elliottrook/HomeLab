# B60 inference candidate-fix register

> Last reviewed: 2026-09-25
>
> Scope: primary upstream sources and explicitly labelled community-provided
> measurements hosted in upstream repositories. A listing is a lead, not proof.

| Candidate / hazard | Primary source and date | Affected version | Applicability and prerequisites | Known risks / rollback | State / project disposition |
|---|---|---|---|---|---|
| Newer llama.cpp Vulkan build | [llama.cpp feature matrix](https://github.com/ggml-org/llama.cpp/wiki/Feature-matrix), reviewed 2026-09-25 | Current upstream vs accepted b11081 | Directly applicable through a side-by-side Vulkan build; requires exact build flags and same model/config fixtures | Vulkan I-quants are still labelled slow; upstream regressions are possible. Roll back by restoring the accepted b11081 binary/unit | Released upstream capability; test after immutable control |
| Standard K-quant/Q4_0 comparison | [llama.cpp feature matrix](https://github.com/ggml-org/llama.cpp/wiki/Feature-matrix), reviewed 2026-09-25 | Current backend support | Applicable if matching Qwen3.8-27B artifacts fit storage/VRAM and pass quality/tool-use gates | Unlike quant comparison; may change quality and memory. Never promote on speed alone; retain IQ4_XS | Supported; source/acquire candidates only after storage and quality gates |
| B60 SYCL reference results | [llama.cpp Intel GPU performance discussion #23313](https://github.com/ggml-org/llama.cpp/discussions/23313), opened 2026-05-19; B60 entries 2026-08-27 | Contributor result at commit `fe235f4` and other later entries | Same GPU generation, but different host/OS/models. Requires a larger physical BAR and matched Intel runtime before it can apply here | Discussion explicitly says results are unverified reference data. Current host cannot enumerate Level Zero. Roll back by removing isolated candidate environment | Experimental lead; BAR-gated, not a current test |
| SYCL FP16/AOT/build controls | [llama.cpp SYCL backend documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md), reviewed 2026-09-25 | Current upstream SYCL | Only after Level Zero enumeration; must record oneAPI/runtime versions and compare correctness | FP16 can alter accuracy; AOT adds complexity/size; host-memory fallback can conceal spill. Use isolated build and disable spill for validation | Documented upstream; deferred behind BAR gate |
| Qwen3.5 SYCL flash-attention crash | [llama.cpp issue #21396](https://github.com/ggml-org/llama.cpp/issues/21396), opened 2026-04-03 | oneAPI 2025.3, llama.cpp `d006858`, B50/B60 | Direct hardware/model-family hazard for any later SYCL trial | Second prompt can crash. Recheck status and reproduce only in an isolated, bounded test; flash attention off is a candidate control, not an accepted fix | Closed stale/not planned; mandatory preflight hazard |
| `xe` OOM/reset hazard | [Intel Compute Runtime issue #842](https://github.com/intel/compute-runtime/issues/842), opened 2025-08-07 | Compute Runtime 25.27.34303.5, kernel 6.15.9, `xe`, Arc B580 report | Same driver family and adjacent GPU generation; relevant to memory-headroom and abort rules | Report describes desktop freeze requiring hard reset after OOM. Avoid spill/OOM; hard timeout and attended recovery for risky compute trials | Open / needs feedback; retain as stop-condition evidence |
| Dell A34 plus explicit Above-4G/Large-MMIO review | [Dell T5810 owner documentation](https://dl.dell.com/manuals/all-products/esuprt_electronics/esuprt_graphics_vdo_crds/dell-8gb-amd-w7100_user%27s%20guide7_en-us.pdf), reviewed 2026-09-25; repository records A34 dated 2020-11-17 | Installed A31; candidate A34 | Exact platform. Requires attended console, verified firmware package/provenance, backup and recovery plan | Release notes do not promise Resizable BAR; flashing/reboot can strand the host. Firmware rollback/recovery must be proven before proposal | High-risk research only; no change authorized |
| One-shot `pci=realloc=on` | Linux PCI allocation behavior; prior project evidence from 2026-08-30 | Kernel/firmware dependent | Only after a reliable attended console path and an independently reviewed boot/recovery plan | Prior GRUB-on-LVM warning showed the one-shot marker might persist; boot/storage/network failure could repeat | Not authorized; decision-tree analysis only |

## Next research actions

1. Pin the latest candidate llama.cpp revisions and inspect Vulkan changes since
   b11081 for BMG, Qwen3.5/3.8, I-quants, KV cache and flash attention.
2. Locate current Mesa ANV/Battlemage release notes or commits applicable after
   26.1.6; do not infer value from a version number alone.
3. Recheck Intel Compute Runtime small-BAR logic and current `xe` BAR-resize/SR-IOV
   work before proposing any platform test.
4. Find same-model, same-quant B60 Vulkan results or record that none were found.
5. Deduplicate every weekly review against this table and record only a changed
   status, new source revision, newly applicable candidate or new hazard.

