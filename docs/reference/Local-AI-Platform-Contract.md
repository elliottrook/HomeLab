# Local AI Platform Contract

> Service identity: `local-ai-platform`
> Service release: V1
> Contract revision: `v1-2026-10-12`
> Status: defined for validation; not yet a production promotion

This is the stable consumer-facing contract for the Local AI platform split.
It separates the service identity and behavior from the current transitional
guest addresses and from any particular model build. The governing project is
[Local AI Platform — Lab/Production Split](../projects/Local-AI-Platform-Split.md).

## Endpoints and environments

Consumers target a platform endpoint supplied by deployment configuration; they
do not hard-code an inference guest address or call llama.cpp directly.

| Contract | Transitional V1 mapping | Future target |
|---|---|---|
| `ai-prod` text gateway | Aster Agent LXC 104, `192.168.70.10:9120/v1` | Stable Aster gateway in `ai-prod` |
| `ai-prod` inference backend | LXC 110, `192.168.70.12:11435/v1`, internal only | Private `ai-prod` backend |
| `ai-prod` speech | Aster canonical voice candidate LXC 116, `192.168.70.14:9131` through the controlled `/voice/v2/` route; legacy `9130` remains rollback/Companion STT | Stable speech endpoint in `ai-prod` |
| `ai-lab` | Whole-host exclusive maintenance lease; no concurrent lab/prod GPU runtime | Separately identified lab endpoint and state |

The transitional mappings are implementation facts, not permission to treat
VLAN 70 as the final production placement. The current accepted text release is
llama.cpp `b11429`, SYCL/Level Zero, Qwen3.5 9B Q4_K_M, one 8,192-token slot.

## Text API

The Aster gateway exposes the bounded OpenAI-compatible surface:

- `GET /health` — unauthenticated liveness only; returns `{"status":"ok"}`.
- `GET /v1/models` — bearer-authenticated model catalogue; returns the stable
  platform model identifier `aster-qwen3.5-9b`.
- `POST /v1/chat/completions` — bearer-authenticated bounded conversation.
  JSON and server-sent-event streaming are supported; callers must tolerate
  bounded response limits and upstream unavailability.

The model identifier is a contract label, not an upstream artifact name. The
gateway owns routing, tool allowlists, response limits and provenance behavior.
Consumers must not rely on llama.cpp-specific flags, model filenames, context
implementation details or internal guest addresses.

## Speech API

The canonical spoken identity is Kokoro ONNX `bm_daniel`, `en-gb`, speed `0.95`.
Piper is a rollback implementation, not a second canonical voice. A speech
consumer must accept a successful response, a bounded timeout, or an explicit
content-free degraded/failure result. Recovery to Piper is an operator-
controlled rollback to the retained 9130 service; consumers must never switch
voices or environments automatically or present Piper as equivalent to the
canonical voice.

The canonical voice service remains at LXC 116 on TCP 9131, with the controlled
HTTPS `/voice/v2/` route and its existing service identity. Legacy TCP 9130
remains active for rollback and Companion STT during migration. The canonical
service uses the pinned Kokoro candidate runtime and renderer boundary; its
model assets are not copied into the legacy service. STT/TTS credentials are
environment-specific and never enter this contract document.

## Authentication and identity

- Every non-health endpoint requires the environment-specific bearer identity.
- `ai-lab` and `ai-prod` use distinct credentials, state and deployment
  identities; a lab token cannot authenticate to production.
- The gateway and speech service keep their existing least-privilege scopes.
- Credentials are supplied through protected runtime configuration only; they
  are never placed in Git, evidence, URLs, logs or browser-visible project
  records.
- A rejected, expired or revoked token fails closed. Clients must surface the
  failure without retrying indefinitely or switching environments implicitly.

## Quotas, timeouts and degradation

The initial V1 envelope is deliberately conservative:

| Area | Contract behavior |
|---|---|
| GPU concurrency | One serving slot; lab experiments require the exclusive maintenance lease |
| Context | 8,192 tokens at the accepted inference baseline |
| Tool use | Gateway-owned bounded allowlist and finite tool rounds; no generic shell/admin access |
| Timeout | Caller supplies a bounded request deadline; the gateway's existing 180-second upstream ceiling remains the hard upper bound until measured otherwise |
| Retry | No blind replay of effectful or uncertain operations; text may be retried only with caller-controlled idempotence |
| Overload | Return a clear unavailable/busy failure or use the documented fallback; do not queue unbounded work |
| Observability | Record aggregate latency, failure and queue signals without prompts, tokens, credentials or principal IDs in metric labels |

Missing telemetry freezes promotion evidence; it is not treated as proof of
healthy capacity.

## Fallback and recovery

Text consumers degrade to a clear unavailable state and preserve the stable
human/operator path. Speech consumers use Kokoro on the canonical 9131 path.
If it fails, the candidate returns an explicit content-free error or
cancellation; an operator may then roll back to the retained Piper/Whisper
9130 service using the documented release procedure. The UI must identify the
rollback/degraded state where that distinction matters. Consumers must not
switch voices or environments automatically, call a lab endpoint, enable a
cloud provider, or broaden credentials.

Recovery order is: control plane and network, stable platform configuration and
artifacts, speech/inference health, then optional consumers. Restore into an
isolated guest or directory first, validate synthetic text and speech, and only
then restore the intended endpoint. A platform restart or host reboot is an
exclusive lab-lease action, even when the experiment is expected to be light.

## Validation gate

This contract is ready for synthetic validation, not promotion. Before marking
the contract milestone complete, test the JSON and streaming schemas, health and
auth failures, quota/timeout boundaries, stable model identity, Kokoro failure
with a content-free error, operator rollback to Piper with explicit degraded
identification, and one consumer's graceful platform-loss behavior. Keep
the current V1 transitional deployment unchanged until those tests and the
separate lab/prod state-separation gate pass.
