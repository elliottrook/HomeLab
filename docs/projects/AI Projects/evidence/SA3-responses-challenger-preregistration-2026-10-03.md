# SA3 Responses API challenger preregistration

Status: **proposed; adapter/corpus/run require separate implementation gates**

The Qwen quality corpus is retired after its result. A future challenger must
use a new private sanitized corpus and the same outcome/control/check rubric.
The adapter will use the OpenAI Responses API with `store: false`, no tools,
no previous response state, no MCP, no web access, and no credential or
infrastructure context. Structured output will use Responses `text.format`.

The adapter must obtain its API credential only from the approved secret broker
at runtime; no credential enters Git, prompts, output, or logs. A development
run must pass schema/conformance checks before one separately authorized fresh
quality run. A pass can qualify only a reversible read-only pilot; it cannot
change policy, permissions, routing, credentials, or execution authority.

Official basis: the Responses migration guide recommends Responses for new
projects, documents `store: false`, and places structured output under
`text.format`.
