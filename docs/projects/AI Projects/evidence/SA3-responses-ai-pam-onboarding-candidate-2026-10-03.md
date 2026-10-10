# SA3 Responses challenger AI-PAM onboarding candidate

Status: **local design candidate; not deployed**

| Field | Candidate value |
|---|---|
| Service identity | `aster.sa3.responses-evaluator` |
| Secret custody | OpenBao only; proposed service-specific path `kv/ai-pam/aster/sa3-responses-evaluator` |
| Granted material | One OpenAI project API credential, injected only for the evaluator process |
| Network scope | Outbound HTTPS to `api.openai.com` only; no LAN targets |
| Capability | One stateless, tool-free Responses evaluation request against a frozen sanitized corpus |
| Prohibited | OpenBao administration, secret enumeration, tools, MCP, web search, previous response state, production action, credential logging |
| Runtime limits | `store:false`; fixed model/configuration; serial; bounded request count; audit metadata only |
| Revocation | Disable identity and revoke/remove the OpenBao secret; preserve human administration |

Before deployment, verify the exact broker binding, outbound egress enforcement,
secret lease/revocation behavior, audit redaction, service account isolation,
and a fail-closed no-secret test. Deployment and creation of the actual OpenAI
credential require a separate bounded infrastructure approval.
