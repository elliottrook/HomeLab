# Qwen3.5-9B B60 screening

Date: 2026-10-10

Status: **screening passed; broader Aster workload comparison required before selection**

Jason approved an immediate Qwen3.5-9B trial on the B60. This was a transient,
reasoning-disabled comparison only. It did not change the accepted production
model, service unit, API key, network policy or scheduler configuration.

## Candidate and controls

- Base model: `Qwen/Qwen3.5-9B`.
- GGUF: LM Studio community `Q4_K_M`, repository revision
  `1379f25c6b505a3fc737bd7818cb09389cf807c1`, 5,627,044,256 bytes,
  SHA-256 `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`.
- Runtime: official llama.cpp b11429 Vulkan archive, commit `d81235049`,
  SHA-256 `632c4e98feba2b94407a2130e3133e0c3aefb0ea1ab41337e926d8bfafdd0b74`.
- Runtime settings: Vulkan, all layers requested on GPU, 8,192-token context,
  one slot, batch 256, microbatch 128, four threads, flash attention, Q4 K/V,
  Jinja, reasoning off and reasoning budget zero.
- Accepted comparison: Qwen3.8-27B UD-IQ4_XS on llama.cpp b11081 with the
  promoted Q4 K/V unit. Its recent authenticated workflows measured
  10.724--10.987 generated tokens/s.

The model and runtime were downloaded only to LXC 110 tmpfs. This preserved the
20 GiB root-disk safety floor. They were removed after the run; available guest
RAM returned to 15,885,662 KiB. Immutable sanitized result files remain in the
protected B60 evidence roots on LXC 110 and LXC 114.

## Safety and recovery evidence

The same-day 02:39 LXC 110 backup and its bounded TrueNAS mirror were present;
TrueNAS task 3 had completed `SUCCESS` at 04:24. Accepted binary and unit hashes
matched, production health was `ok`, the B60 was bound to `xe`, Vulkan identified
the discrete BMG G21, and no relevant recent kernel failure was found.

The hourly news timers were stopped only for the live load. A trap stopped the
candidate, quiesced the device, restarted accepted production, waited for
health, and restarted both timers. Post-run checks proved:

- accepted service active and candidate inactive;
- accepted binary and promoted-unit hashes unchanged;
- endpoint health `ok`;
- both news timers enabled and active;
- B60 still on `xe` and enumerated as discrete BMG G21 through Vulkan;
- no reset, hang, fault, device-loss or OOM line during the trial; and
- 21,920,120,832 bytes of root-disk headroom remained.

## Screening results

Raw llama-bench medians/averages reported 661.644 prompt tokens/s at pp512,
564.805 prompt tokens/s at pp4096 and 46.795 generated tokens/s at tg128.

The authenticated OpenAI-compatible runner then performed one warm-up and five
measured repetitions for each workflow. Every recorded assertion passed:

| Fixture | Median prefill | Median decode | Median decode time | Result |
|---|---:|---:|---:|---|
| Aster conversation | 581.562 tok/s | 47.845 tok/s | 4.229 s | pass |
| Aster persona | 39.646 tok/s | 47.805 tok/s | 3.518 s | pass |
| Read-only tool selection | 577.483 tok/s | 47.114 tok/s | 1.923 s | pass |
| 2K grounded retrieval | 604.480 tok/s | 45.387 tok/s | 3.795 s | pass |

The persona prefill case contains only a very small prompt despite the fixture's
nominal construction target, so its prefill rate is not comparable and is not
used for the decision. The other figures show an approximately 4.2--4.5x decode
increase over the accepted 27B authenticated workflow rates. This is a material
efficiency lead, not a production-selection result.

## Decision and next gate

Qwen3.5-9B Q4_K_M is technically viable on the B60 and is the preferred local
challenger. This run proves model loading, Vulkan operation, substantial speed,
basic persona behavior, one structured read-only tool call and simple grounded
retrieval. It does not prove personal-summary quality, ambiguous timer/media
handling, privacy routing, long-document reliability, overnight reasoning or
equivalence to the current 27B model.

Before selection, compare the 9B and accepted 27B models on a frozen synthetic
Aster-local suite covering deterministic intent extraction, ambiguity/refusal,
media and Home Assistant routing, personal calendar/email/news summarization,
grounding and explicit sysadmin-to-GPT escalation. Run reasoning off for the
interactive arm and a separately bounded thinking arm for overnight analysis.
Require zero unsafe tool decisions and human review of semantic quality; do not
promote from substring assertions or throughput alone.
