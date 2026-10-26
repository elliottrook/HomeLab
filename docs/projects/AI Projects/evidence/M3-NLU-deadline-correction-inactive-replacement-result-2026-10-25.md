# M3 NLU deadline correction inactive replacement result — 2026-10-25

Status: **PASS — INACTIVE PACKET REPLACED; LIVE CALIBRATION STILL CLOSED**

Jason approved the replacement packet described by
`M3-NLU-deadline-correction-inactive-replacement-card-2026-10-25.md`.
The transaction from Stream A commit `ff6c12e1` completed on LXC110 at
2026-10-26T04:55:39Z.

## Result

- Source correction: `682608d2`.
- Installed runner SHA-256:
  `a8cca4daa3a0504b07e9dc70bee4d8e04d3f181ac742c53954718c6918fc5a0f`.
- Staging manifest SHA-256:
  `05aa0f287795dacfa72c37d7b275a85f67e96f0cc253225dcf78908585970e19`.
- The exact 11 manifest inputs independently matched by name and SHA-256.
- Every staged input is a root-owned mode-`0600` regular file in the
  root-owned mode-`0700` run directory.
- The generated `__pycache__` is absent from the run directory.
- `run.json`, `attempt-journal.jsonl` and a runner process are absent.
- `aster-llama.service` remained active and `local-ai-lease status` remained
  `ready`.

The old runner and generated cache were retained in the owner-only checkpoint
`/var/lib/aster-nlu-calibration/checkpoints/deadline-682608d2-20261026T045539Z`.
The preserved runner SHA-256 is
`b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11`.

## Schedule isolation

The replacement did not change the October 26 F2 chain. The date-specific
prepare and final timers remained scheduled for 01:15 and 01:20 PDT,
respectively. LXC104, LXC110 and LXC116 remained running; `pvescheduler` and
`pvestatd` remained active.

This result proves inert custody and target-Linux validation only. It does not
authorize or perform a model request, lease acquisition, service restart,
threshold registration, holdout access, routing promotion or F6 activation.

