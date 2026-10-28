# SA1–SA3 Forgejo expansion installation and connected result — 2026-10-28

## Result

**PASS.** Jason approved the exact five-file Forgejo expansion and one restart
of `aster-agent.service`. The reviewed release installed successfully, retained
the four exact predecessors in its root-only rollback checkpoint, and passed
an independent installed four-source investigation.

## Installed release

- release ID: `sa1-sa3-forgejo-expansion-20261028`;
- manifest SHA-256:
  `323243795ecd945c5eee184057e01df2219daed64892e6d69dd45e030aed4059`;
- packet SHA-256:
  `6e549542fd7892ab81938d89f87bb9e443c721aea3406f074feb4b7cf8c39e24`;
- installer SHA-256:
  `6fa786542b2798dfa7207067e3f8142a93a34b012bfc5af5771bbd0ed62fd4e9`.

The installed files are root-owned mode `0644` and match the reviewed hashes:

| File | SHA-256 |
|---|---|
| `aster_agent.py` | `75d49b81ce7e277ff67dfe0f929536f94835dc93c710c6206aa558259208261d` |
| `forgejo_incident_adapter.py` | `e0944352e8304d25e5f55b74d88df700cd1b64ad3fdedc784aa7c66486f25809` |
| `sysadmin_registered_producer.py` | `27175ab0d1a0cbcfc1fbc3201859417e2818b22d1738f1d2d2dc3a48f8191c96` |
| `sysadmin_proposal_boundary.py` | `2050cd7e12b5207dce21c5087d4e643ffa85965376d415c0ed7ee673d9894515` |
| `sysadmin_proposal_transport.py` | `dca6a28c3096fc398f49cbdc33ddb1f26ff09b559870566281d7bec42be1c6be` |

The checkpoint `/var/lib/aster/sa1-sa3-pre-forgejo-expansion-20261028` is
root-owned mode `0700` and contains the four exact predecessor hashes from the
release manifest. The adapter was absent before installation and is removed by
rollback.

## Independent connected check

The isolated installed loop used a temporary mode-`0700` incident store and
completed this bounded sequence:

| Step | Target/kind | State | Decision |
|---|---|---:|---|
| Seed | `homelab-doctor/status` | `fail` | registered sanitized report |
| 1 | `forgejo-main/git` | `ok` | observe, authority/effect none |
| 2 | `aster-gateway/status` | `ok` | observe, authority/effect none |
| 3 | `inference-server/status` | `ok` | observe, authority/effect none |
| 4 | null | n/a | complete, authority/effect none |

The terminal result contained four decisions, three consumed observations and
four observations. Model health and idle checks passed after the request. The
temporary runner, helper, packet, installer and state were removed.

## Production postchecks and scope

- Aster Agent is active/running on new PID `28087`, restart count `0`, with its
  exact `status=ok` health response.
- The accepted llama.cpp/SYCL service remained active/running on unchanged PID
  `61089`, restart count `0`, with health `ok`.
- The whole-host lease remained `ready`.
- No model, model service, automatic route, repair authority or generic tool
  authority changed.

This closes the first representative source expansion. Backup, network, log
and configuration breadth remain separate registered-source milestones.
