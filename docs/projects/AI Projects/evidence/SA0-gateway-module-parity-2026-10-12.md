# SA0 gateway imported-module parity — 2026-10-12

**Scope:** read-only production hashes and a local source correction. No production file or process changed.

After the gateway file reached exact source parity, its nine directly imported local modules were compared with the deployed files in LXC 104. Eight matched by SHA-256: `arr_report.py`, `ha_report.py`, `source_reports.py`, `broker_approvals.py`, `doctor_incident_adapter.py`, `sysadmin_incident_store.py`, `sysadmin_incident_stream.py`, and `sysadmin_investigation.py`.

`lab_operations.py` differed in two ways. The branch contains an operator-only `reconcile_interrupted_doctor` method absent from production. It has no HTTP/model path and remains an **uninstalled candidate**; its presence must not be described as a live recovery capability. The deployed module already labels synthetic Lab Operations completion responses `aster-qwen3.5-9b`, while branch source still said `aster-qwen3.8-27b`. Only those two local response metadata literals were corrected to the deployed/current 9B label. The local file therefore still intentionally differs from production and must not be copied wholesale into LXC 104.

The focused Lab Operations suite passed **23/23** after the metadata correction, and `git diff --check` passed. Hash equality for the eight modules proves source parity at this checkpoint, not runtime behavior or deployed package parity. Later deployment of the operator-only method needs its own operational gate; this record does not authorize it. Forgejo synchronization of this local commit requires per-push confirmation.
