# AI-PAM service-registry entry

Copy this template into the service's project or operational record. Do not
store credentials, recovery material, tokens, private keys or secret-bearing
output here. One entry represents one service integration and its explicitly
bounded capability set.

## Service and ownership

- Service:
- Service owner/operator:
- Authoritative service record:
- Integration status: proposed / candidate / pilot / active / suspended / retired
- Last reviewed:
- Review owner/date:

## AI authority

- AI administration posture: brokered / dynamic / static exception / not currently supported
- AI service identity (or reason unsupported):
- Authentication type:
- Broker execution mode: proxy / dynamic / wrapped-static / none
- Human break-glass path:

| Capability | Target/scope | Risk class | Approval/freshness | Allowed arguments | Explicit denials |
|---|---|---|---|---|---|
| | | Green / Yellow / Red / Black | | | |

## Credential custody

- Secret custody identifier (never the value):
- Source-local consumer:
- Rotation trigger and procedure:
- Revocation procedure and expected propagation time:
- Recovery dependency/order:
- Static-credential exception reason and review date, if applicable:

## Network and data boundary

- Broker-to-target path:
- Required DNS/certificate/firewall facts:
- Data returned to the AI:
- Sanitization/schema limit:
- Audit metadata retained:
- Prohibited output:

## Validation and lifecycle

- Allowed-action test:
- Denied scope/argument/identity tests:
- Approval replay and changed-payload tests:
- Target-side and broker-side revocation tests:
- Dependency outage/fail-closed test:
- Backup/restore evidence:
- Two independent production passes, when required:
- Temporary access removed:
- Residual risk/accepted limitation:

## Integration impacts

Record change or `not applicable — reason` for Doctor, monitoring, backup,
NetBox, wiki/mirror, operational runbooks, repository architecture, Homepage,
authentication, DNS/certificates/firewall, schedules and security inventory.
