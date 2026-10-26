# M3 NLU 27B semantic development result

**Date:** 2026-10-26  
**Decision:** **NO-GO — reject before cross-set evaluation**

## Approved transaction

Jason approved the exact bounded switch in the
[source run card](M3-NLU-27B-semantic-development-run-card-2026-10-26.md).
Fresh gates found the whole-host lease ready, LXC110 running, the accepted 9B
service active with zero restarts and both fresh staging/result paths absent.
The controller and packet hashes matched before use.

The controller armed recovery, stopped the accepted 9B service, started the
retained Qwen3.8-27B IQ4_XS Vulkan candidate as a transient unit, waited for
health and ran the 24 public synthetic cases once. It then stopped the transient
unit and restored the accepted 9B/SYCL service through its exit trap.

## Result

- attempted and structurally valid: **24/24**;
- exact interpretations: **9/24**;
- routed: **12/24**;
- safe and exactly correct routed: **7/12**;
- unsafe false routes: **2**;
- routed privacy underclassifications: **0**;
- run SHA-256:
  `937586ec4ee10b0c1b39292423b23373b60a567d1208a8e2b995ff6bd3afdb27`.

The candidate fails both the 23/24 accuracy requirement and the zero unsafe
false-route requirement. The two unsafe routes were in unsupported fictional
request classes. Other content-free mismatches covered capability selection,
ambiguity/disposition, family and sensitivity. There is no retry, prompt repair,
cross-set evaluation, new calibration, holdout access or promotion.

This also shows that model size alone does not repair the semantic-slot
architecture: the 27B result matched the 9B result's 9/24 exact score and was
worse on unsafe routing. Further work needs a different representation and a
more effective deterministic incomplete/unsupported envelope, not another
prompt variant on these models.

## Independent restoration checks

After the controller returned:

- `aster-llama.service`: active, `NRestarts=0`;
- transient `aster-b60-candidate.service`: inactive;
- accepted unit SHA-256:
  `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`;
- accepted SYCL binary SHA-256:
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`;
- `/health`: `ok`;
- `/v1/models`: only the accepted Qwen3.5-9B Q4_K_M path;
- Aster Agent and Aster Speech: active;
- whole-host lease: ready.

No persistent unit, timer, schedule, model, key, grant, route or application
changed.
