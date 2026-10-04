# SA3 local-only operational decision

Status: **adopted for the current programme; cloud challenger deferred**

ChatGPT subscription use cannot fund a local API integration, and the local Qwen
candidate failed the operational-quality gate. Stream A therefore adopts a
local-only operational path:

1. deterministic intent matching identifies bounded lab-diagnosis requests;
2. the existing AI-PAM broker permits only registered read-only evidence
   collection;
3. the Doctor adapter and typed incident store retain provenance, freshness,
   observation limits, and a proposed next read-only step;
4. a human reviews the resulting incident packet and remains the only authority
   for remediation.

No LLM is in the authority or operational-diagnosis path. Qwen remains usable
only where separately evidenced for constrained local assistance. The proposed
Responses challenger is deferred without deployment, credential creation, or
cloud request.

Fourteen typed-investigation, persistence/retention, and Doctor-adapter tests
passed in the bundled workspace runtime. The two FastAPI gateway suites remain
**UNKNOWN** there because FastAPI is absent; nothing was installed. The deployed
LXC does not retain test files, but its Doctor adapter, typed investigation, and
incident store exactly match the current source hashes. The next delivery gate is a finite authenticated Doctor
read-only pilot with freshness/deduplication evidence; it needs its own
deployment and observation approval.
