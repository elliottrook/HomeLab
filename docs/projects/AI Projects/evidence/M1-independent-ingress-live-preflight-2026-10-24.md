# M1 independent ingress live preflight — 2026-10-24

Read-only checks against Proxmox and LXC 104 found:

- `aster-approval` user/group and UID/GID 1905 are absent;
- the existing `hlabroker-approvers` group still contains `hlabroker,aster`;
- the main broker, existing approval broker and Aster are active and enabled;
- the existing approval broker still accepts peer `aster`, uses
  `/run/homelab-broker/approval.sock`, and loads
  `/etc/aster/broker-approver.env`;
- Aster listens on `192.168.70.10:9120`; nothing listens on 9121;
- Nginx Proxy Manager proxy-host 18 points to 9120 and contains no 9121 target;
- Proxmox cluster and LXC 104 firewall rule lists are empty; this does not prove
  the upstream routed firewall would permit 9121;
- `/etc/aster` is 0750 root:`aster`, the current broker approver environment is
  not reused in place, and the broker database remains 0600 `hlabroker`;
- the live Aster environment has FastAPI 0.133.1, HTTPX 0.28.1, PyJWT 2.14.0,
  Pydantic 2.13.4 and Uvicorn 0.41.0;
- the repository `broker_approvals.py` matches live; the two approval-ingress
  Python modules and both candidate units are absent; and
- the live broker-approval implementation still differs from repository source,
  so the inactive stage deliberately does not replace it.

These facts support the bounded inactive installation card. They do not establish
network reachability, a safe traffic cutover, independent passkey assurance or a
connected-tool grant. No configuration value, subject hash, token or approval
payload was read into the record, and no live state changed.

