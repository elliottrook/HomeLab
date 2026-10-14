# A1 Aster source bundle inventory — 2026-10-14

**Status:** source inventory only; no bundle installed or model call made.
This inventory concerns the **Stream A candidate** at commit `e6b638e4`.
It is not proof that the deployed LXC 104 Aster has the same source.

Static Python import traversal from `aster_agent.py` found these 11 local
top-level modules. The listed SHA-256 values are from this worktree. Copying
the entire `services/aster-agent` tree would add unrelated source; the
reviewed sidecar bundle should use this exact closure plus the four guarded
A1 modules and its separately pinned Python dependency environment.

| Local module | SHA-256 |
|---|---|
| `arr_report.py` | `adacab07f40b1218be43fd5d4119efc87571ffba06b41151d40f3cc099c231d9` |
| `aster_agent.py` | `d6a05bcc7edddb1eaa69a67450cfc48c1c0e96ba8688de7a1246a1e9eb847e11` |
| `broker_approvals.py` | `cf37fb1782c875622155b50d7b69f31b7c9acc2c30f7881f5da9b4a6538dd324` |
| `companion_notifications.py` | `c0b850d39e50c5a84eb1a54c322ce8ccae306b638d5013b26afe63788fe3b5b4` |
| `doctor_incident_adapter.py` | `c88c4e642426afff9718da79e89db5b8405f1a5c00fbcc0fa09c3ae5956272db` |
| `ha_report.py` | `9d99e511a123fb5a73c93aceb17af7ea7ebbeb442e437798b2c5cfadbdeece81` |
| `lab_operations.py` | `bb57475cf8f3dac16e793598f744ce8cd4627997becf64ee64b2858056f30dc1` |
| `source_reports.py` | `7a85c52a5b350f3dde81b52fdd118f9a37f9a45feaca50db4f86092a297eadd2` |
| `sysadmin_incident_store.py` | `4e8a36a803c3d8e5eac362e4c17a0cadc1f4ae2accca05cc73283b646b8e5c4b` |
| `sysadmin_incident_stream.py` | `8aa8c572cbe3208b9b8c1a0ce34dfdab893a064ba79e7e5a87c7d8decca8d683` |
| `sysadmin_investigation.py` | `bfd5e9675b4a7ef06aa0ddb28e7c9b5fda2076a86957cd5474a75ccbd50ee6fe` |

`requirements.txt` in Stream A hashes to
`a1beddbeac7ac0afc27f3659b41defe0af9f5dcbf9fb91516cd86d9f4ace2929`.
It pins FastAPI, httpx, Pydantic, Uvicorn, PyJWT and pywebpush. The installed
wheel versions and hashes for a sidecar virtual environment remain
**UNKNOWN / REQUIRES VERIFICATION**; this list alone is not a reproducible
dependency lock.

**Verified current state:** a read-only LXC 104 SHA-256 check returned
`b0b81467d3e06c5277a3a60a70530af28fe67ac1775c6f40694a52da080d405a`
for `/opt/aster-agent/aster_agent.py` and
`28433903f3dd33a33a4264f892f1d24f777a472d5cc5c315d05d8e23e3e7d1`
for its `requirements.txt`. Neither digest matched any version of the same
path in this checkout's reachable Git history (`git log --all -- path`). The
deployed file contents and their provenance were not inspected. The current
main working-tree `aster_agent.py` also has a third digest; it is not a
validated deployment source.

**Admission consequence:** a benchmark using the Stream A candidate would
measure that pinned candidate, not the currently deployed Aster instance.
Before any full-path run, select and label one baseline explicitly:

1. **Deployed-runtime baseline:** obtain a protected, reviewed source and
   dependency snapshot of the live LXC 104 instance, prove its hashes and
   test-only isolation, then run it in the sidecar; or
2. **Stream A candidate baseline:** use this exact worktree source and a
   reproducible dependency bundle, and label all results as candidate-path
   evidence. Do not describe them as current-production Aster performance.

The ordinary Aster production process remains untouched. This is a source
identity decision, not permission to install or run either bundle.
