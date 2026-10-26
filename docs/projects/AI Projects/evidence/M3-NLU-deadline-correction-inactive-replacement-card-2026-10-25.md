# M3 NLU deadline correction inactive replacement card — 2026-10-25

Status: **SOURCE READY; TARGET CHANGE NOT YET AUTHORIZED**

This card replaces only the inert staged calibration runner after the
[post-journal deadline correction](M3-NLU-post-journal-deadline-correction-2026-10-25.md).
It also removes the four-file `__pycache__` directory created after the earlier
staging result. The cache appeared at 2026-10-26T04:07:20Z; no runner process,
`run.json` or `attempt-journal.jsonl` exists, the accepted llama service is
active and the whole-host lease is ready.

## Exact change

- Target: LXC110
  `/var/lib/aster-nlu-calibration/nlu-calibration-v1/nlu_calibration_runner.py`.
- Required old SHA-256:
  `b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11`.
- New source commit: `682608d2`.
- New SHA-256:
  `a8cca4daa3a0504b07e9dc70bee4d8e04d3f181ac742c53954718c6918fc5a0f`.
- New manifest SHA-256:
  `05aa0f287795dacfa72c37d7b275a85f67e96f0cc253225dcf78908585970e19`.
- New validator SHA-256:
  `487341d1d35fa7ee313aeb76816162048e2402a985a801f6053e3ea89a971e80`.

The other ten staged input files must match their existing manifest hashes,
root ownership and mode `0600`. The run directory must remain root-owned mode
`0700`.

## Transaction and rollback

Use only
`scripts/aster-adaptive/install_nlu_calibration_deadline_correction.sh` at its
SHA-256
`8b6c69c8eb9777d9de8c69a16f192a609cf3b706072fe4f25f66633b6ec261c9`.
It must:

1. require the exact old packet, the known generated cache, absent outputs,
   no runner process, active llama service and ready lease;
2. preserve the old runner and cache in a new root-only LXC110 checkpoint;
3. replace the runner atomically and remove the cache from the run directory;
4. validate the exact eleven-file directory using the new manifest and
   validator with `python3 -B` and `PYTHONDONTWRITEBYTECODE=1`;
5. import every staged module without creating bytecode; and
6. verify absent outputs/processes, active llama and ready lease.

Any failure restores the old runner and cache and removes only temporary
transport files. The checkpoint is retained after success.

This change does not start a runner, read the local service key or private case
contents, acquire a lease, call the model, score results, create a threshold,
enable routing, restart a service, arm F6 or change tonight's F2/F3 schedule.
