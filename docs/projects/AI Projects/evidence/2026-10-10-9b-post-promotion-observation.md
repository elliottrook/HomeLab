# Aster 9B post-promotion observation

Date: 2026-10-10

Status: **operational gates passed; identity correctness failure remediated and revalidated**

## Outcome

The owner requested that the scheduled final observation and publication be
performed immediately. The read-only observation confirmed the accepted
production configuration and found no infrastructure or GPU fault:

- active unit SHA-256:
  `6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e`;
- b11429 server SHA-256:
  `5faf410bbbc00a1b94b09ee01623699f255365628dfa73b1ee552d9e52a2231d`;
- model SHA-256:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- former-27B rollback unit SHA-256:
  `e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184`;
- Aster source SHA-256:
  `a311a020ccf4965e7d1efee43bcbaacfc7b6f95379bba87daaf082eec5ea4b66`;
- inference and Aster services active with zero restarts;
- endpoint health `ok`;
- B60 bound to `xe` and enumerated as Intel Arc Pro B60 BMG G21 through
  the Mesa Vulkan driver;
- device-local heap 23.66 GiB with a 16.84 GiB budget reported after model
  load;
- 21,943,644,160 bytes of root-disk availability and 9,045,840 KiB of
  available RAM;
- both News timers active;
- no matching reset, hang, fault, device-loss or OOM kernel event since
  promotion.

## Failed correctness gate

Authenticated model discovery correctly returned `aster-qwen3.5-9b`, and the
chat result carried model `aster-qwen3.5-9b` with runtime fingerprint
`b11429-d81235049`. The generated sentence correctly named Qwen3.5-9B,
llama.cpp and the B60 Vulkan path, but incorrectly said that inference runs in
LXC 104. The documented architecture and deployed system prompt correctly
place the Aster interface in LXC 104 and llama.cpp inference in LXC 110.

An earlier authenticated identity check returned LXC 110 correctly. The new
sample therefore exposes intermittent factual correctness rather than a stale
deployed prompt or metadata problem. The observation is not a pass and must not
be represented as final closeout.

No service restart, reset, retry, model change or other production mutation was
performed. The finite validation automation remains active for the next
read-only observation. Any remedy must be addressed in Aster's deterministic
identity handling or response contract rather than by treating another sample
as proof that the issue is absent.

## Approved remediation and final validation

Jason approved the production behavior change. A narrow deterministic handler
now recognizes explicit runtime-identity questions and returns a versioned
static response that distinguishes the Aster interface in LXC 104 from local
Qwen3.5-9B/llama.cpp inference on the B60 Vulkan path in LXC 110. It also names
VM 105 as the stopped Ollama rollback guest. Other questions retain the normal
model and tool routes.

Four focused tests passed inside Aster's deployed virtual environment: exact
identity content, conservative intent matching, model/tool bypass and streaming
framing. The existing 75 Aster evaluator and 27 B60 harness tests also passed.
The deployed live-preserving source SHA-256 is
`4bad7c6e8cdf9e89a1cde25014ce2d8ed5808dd3666bbf5fd47cf64698ced2a4`;
the pre-change source is retained at
`/opt/aster-agent/aster_agent.py.pre-runtime-identity-20261010` with SHA-256
`a311a020ccf4965e7d1efee43bcbaacfc7b6f95379bba87daaf082eec5ea4b66`.

Authenticated validation of the exact failed prompt and a second wording both
returned the same correct response with fingerprint
`aster-deterministic-runtime-identity-v1`. A negative-control request about why
smaller models are faster bypassed the handler and used the actual 9B/b11429
backend at 46.3 output tokens per second. Both services remained active with
zero restarts, inference health was `ok`, and the kernel fault scan was empty.
The correctness blocker is resolved and the finite automation can be paused.
