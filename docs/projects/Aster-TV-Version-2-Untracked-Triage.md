# AsterTV v2 untracked script triage — 2026-10-29

Nineteen untracked Python files remain in this worktree from the production
regression investigation. They are preserved as local evidence, excluded from
the SHA-pinned v2.0.2 archives, and are **not** an installation queue. Several
write directly to production Kodi paths and would be unsafe to run as a batch.

| Files | Finding and disposition |
| --- | --- |
| `services/kodi/v2/tools/diagnose_prod_digest_handoff.py`, `diagnose_prod_series_entry.py`, `trace_prod_digest_route.py` | Historical production diagnostics. Retain locally for comparison; no release runtime dependency. |
| `services/kodi/skin.asterhome/tools/youtube_landing_focus.py` | Experimental focus helper. The current tracked successor uses `youtube_root_focus.py`; do not add this alternate helper to the package. |
| `services/kodi/v2/tools/repair_prod_youtube_{browse,default,entry,event,event2,focus,focus_wait,layout,root_route,session_focus,session_focus2,session_focus3,session_focus4,shared_focus,titles}.py` | Fifteen successive production repair experiments, several referencing the alternate helper. Retain locally as investigation history; the tracked successor and current lab behavior determine release code. Do not run these against v1.1.1 production. |

The current code-only archive has 657 unique members and 12 add-on roots. No
untracked file was silently incorporated. A later cleanup can move these files
to an explicit historical archive or remove them after their evidence is no
longer needed; that is separate from the current v2 release candidate.
