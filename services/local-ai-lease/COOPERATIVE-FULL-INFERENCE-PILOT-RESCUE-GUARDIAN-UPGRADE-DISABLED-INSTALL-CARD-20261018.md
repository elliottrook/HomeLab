# Pilot rescue and deadline-guardian upgrade — disabled-install card

Status: source-only upgrade candidate. This card is separate authorization
from the already staged `b43d4971` pilot packet. It does not authorize a live
pilot, guardian prearming, timer creation, service changes, or a remote push.

## Exact base and delta

The target currently has the b43d4971 pilot packet installed. Preserve a
recoverable checkpoint before replacement. Replace/add exactly these four
files under `/usr/local/libexec/local-ai-lease/full-inference-pilot/`; do not
touch any other staged file:

| File | Current b43d4971 SHA-256 | Upgrade SHA-256 | Action |
|---|---|---|---|
| `full_inference_lab_runtime.py` | `ff65b3653b338fc658e6bbbe10082a9a771026295a73aeb408f58be8a9e3ceda` | `55feabc1175bd4c1e4cc97f27eae9d3ee3704a2291c514d885f9f88ef49c7cdc` | replace |
| `test_full_inference_lab_runtime.py` | `6f9596fcd52455c1868f7d57e6a4a3aede9fd97956f6b51b640bc7fd1e217db0` | `3efc850f9e8f42fa5aec2e74fa2083fa1c4ff2e6f491004aec10a6345a2eba` | replace/evidence |
| `full_inference_lab_deadline_guardian.py` | absent | `8a003024a2c2a2e191d85389c3022e61322a5f33710712249d37eb9692c6e50f` | add |
| `test_full_inference_lab_deadline_guardian.py` | absent | `a44cdaf240ce3a8b2ce1cdd3679bef46cc7d0ac9e6774c93a55a13b5637437e5` | add/evidence |

The upgrade source tip is `b67373c4`. Runtime files remain `root:root` mode
0644 in the existing root-only directory. This upgrade creates no systemd
unit or timer and does not prearm the guardian.

## No-effect verification

Run the focused rescue/guardian tests and the complete local-AI suite from an
isolated copy. Verify the rescue parser, exact owner/lease/generation binding,
owner-scope fencing, zero-task/zero-MainPID proof, pre-lease arming, owner
token `0`, near-deadline timeout bound, and failed-fence retention tests.
Verify the installed hash table after replacement and confirm the existing
manual lease remains `ready`, all five production consumers remain active, and
port 11436 has no listener. No model call, scope, service stop, timer, or
network change is permitted during this upgrade.

## Rollback and promotion gate

Rollback restores only the b43d4971 checkpoint for these four files. Preserve
the guardian source separately if rollback is uncertain; do not run it. A
successful disabled upgrade is still not live authorization. Before a pilot,
the operator must prearm the exact owner scope and one-shot guardian from the
combined run card, observe both units, and record the guardian deadline and
rescue result. If either unit cannot be independently observed, the pilot is
NO-GO. No recurring watchdog or timer is authorized by this card.
