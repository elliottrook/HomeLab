# SA3 Responses challenger deployment preflight

Status: **read-only preflight complete; deployment blocked on external credential**

## Verified current state

- LXC 104: `aster-agent`, `homelab-broker`, `homelab-broker-approval`, and the
  bounded Lab Operations broker gateway are active.
- LXC 117: OpenBao is active and listens only on loopback plus `192.168.50.24`.
- Repository evidence does not identify an existing Responses evaluator identity,
  service unit, OpenBao policy/path, or egress rule.

## Blocker

No OpenAI project API credential was supplied or discovered, and no secret was
read. Creating a secret or calling the service without a user-provided,
project-scoped credential is impossible and would violate the proposed custody
boundary.

## Required bounded deployment package

1. user creates an OpenAI project API credential for this evaluator;
2. a human administrator writes it only to the approved service-specific OpenBao
   path;
3. deploy an evaluator service identity with broker-only retrieval and audit
   redaction;
4. enforce outbound HTTPS only to `api.openai.com`;
5. test no-secret, revoked-secret, and disabled-identity failure modes;
6. run no model request until the new private comparison corpus and one-run
   authorization are separately frozen.
