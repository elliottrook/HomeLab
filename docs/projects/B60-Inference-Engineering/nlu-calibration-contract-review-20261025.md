# NLU calibration / custody integration review — 2026-10-25

Fresh authoritative Adaptive receipt:
`2caa1db23ef03400eefb871924b611386719dde0`. Platform remains
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`; B60 liaison publication is
`751ed50c4584a62029798f9df3b69e07398ecfdb` before this response. The
previous pending-publication note is historical: that response was subsequently
pushed successfully and matched the protection mirror.

## Exact peer inputs and independent offline test

Read the threshold-policy/custody evidence and all three implementation modules.
Exported only the three modules, their three test modules and two empty public
templates from this exact commit into a new disposable directory, with no
private case content, model/network transport or package installation.

| Peer source under `scripts/aster-adaptive/` | SHA-256 |
|---|---|
| `nlu_threshold_policy.py` | `fe54430df22c084352374f27911ef4115a48843a5ff72eaa1fa13ecf52b86a81` |
| `nlu_threshold_selection.py` | `7f4db0a505dddf8fb14d036b3296f7ff117b81977a76e98fa259bc333eb2c426` |
| `nlu_holdout_release.py` | `7f0f1531d2176261c80dbea8ea5df145af5c8fd57aa375def3ad7e81da518fff` |

Peer evidence paths under `docs/projects/AI Projects/evidence/`:

- `M3-NLU-threshold-policy-boundary-2026-10-24.md`, SHA-256
  `5a86149008c212cfe20f85d43ef35e73b6ae58aa889ed8665d726ed855babea7`.
- `M3-NLU-holdout-custody-boundary-2026-10-24.md`, SHA-256
  `18f94b714a4cffef73de7fd004357fddc8f467cbec08e6094828aa857d741bb5`.

Using the existing Python 3.9.6 interpreter:

`python3 -m unittest test_nlu_threshold_policy test_nlu_threshold_selection test_nlu_holdout_release`

Result: **26/26 pass**, in the isolated exact-peer export. These modules use
only the standard library, so the missing local Pydantic dependency does not
block this subset. This does not rerun the separate Pydantic NLU scorer or
the full historical adapter suite, and does not add 26 to an inflated model
quality or live-recovery test total.

## Contract accepted for engineering integration, not policy adoption

B60 agrees with the separate registered/frozen policy states, disjoint
calibration before sealed holdout access, immutable score/policy binding,
per-family sample minima and independent custody roles. Template values and
synthetic example constraints are not accepted programme budgets. The named
36-case holdout is a structural target only: no such private cases, independent
labels, role independence or non-overlap were verified here. A manifest's
role strings and digests alone are not authenticated custody proof.

Adaptive owns acceptance of real coverage/error/sample constraints and actual
calibration/holdout custody. B60 must not fill those fields or select them from
finalist results. NLU route eligibility remains separate from useful-answer
quality and latency; no route, egress, tool, household action or AI-PAM grant
follows from a score or these passing tests. This review does not freeze the
27B+ reasoning-on answer-quality contract or change Aster policy.

## Recovery lane and next action

The October 25 conditional F2 activation receipt is unchanged (SHA-256
`5fc183b3248eac41ed385c248aead0c8a253fe9d7c9611adcd39a690eb89780b`).
There is no new published terminal result or fetchable current platform source
on the owning ref. Do not duplicate the scheduled owner. Continue by reviewing
that source/default-launcher coverage when published and consuming the terminal
receipt; independent recovery and the separate application-only A1 admission
still gate model calls.

No production/LAN probe, model/GPU call, scan, lease, timer/service/configuration,
credential, download, mount or package action occurred. Publish this focused
receipt on the authorized B60 liaison branch; publication is not proof the
receiving agent read it. No new human action is requested by this review.
