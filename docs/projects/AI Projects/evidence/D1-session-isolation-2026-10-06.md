# D1 offline session and configuration checkpoint — 2026-10-06

## Verified results

31 offline unit tests pass in `services/aster-agent/delegation`.
The session coordinator now connects durable claims to event handling. It buffers
bounded final-answer events before a turn acknowledgement, excludes reasoning
payloads, persists a matching terminal status before exposing an answer, rejects
duplicate dispatch, and classifies documented subscription/rate/auth failures.
Cancellation still requires a terminal acknowledgement. Unknown dispatch does
not automatically retry. This is fixture evidence, not a running bridge.

An installed app-server configuration-only probe tested a restriction profile
in a temporary empty working directory. No thread or turn was created. It
confirmed all 15 requested feature disables, disabled web search, and requested
read-only sandboxing. Initially one inherited MCP connection remained enabled.
An explicit inline-TOML MCP restriction reduced the effective enabled count to
zero. No inherited instruction string was reported in the three checked config
fields. This does not prove absence of all discovered skills or global documents.

The first per-server override syntax caused startup disconnection. It was
replaced with an inline TOML table and the configuration read succeeded. Raw
stderr, MCP names, account details and configuration contents were not logged.
Diagnostic output uses fixed categories only. No saved configuration, production
infrastructure or credentials were changed.

Final metadata summary:

```json
{"disabled_flag_count":15,"unconfirmed_flag_count":0,"initial_enabled_mcp_count":1,"enabled_mcp_count":0,"web_search_disabled":true,"read_only_requested":true,"inherited_instruction_present":false,"tool_isolation_proven":false,"inference":false}
```

## Remaining gate and exact resume

D1 remains incomplete. Effective configuration is not a complete inventory of
tools exposed to a model or proof of operating-system isolation. In particular,
read-only sandboxing is not a blanket ban on reading local files. Before D2:

1. Establish an inspectable effective tool/context boundary for the exact child
   session, including built-in tools not covered by feature flags. Do not infer
   this from “please do not use tools” or from zero MCP connections.
2. Wire the coordinator to a bounded event transport with interruption and
   reconciliation. The existing metadata client deliberately rejects turn/start.
3. Add restart recovery using thread/turn status, persist the approved fixture
   fingerprint/model/settings, and prevent transcript loss from becoming replay.
4. Finish the D2 executable manifest using the already preregistered fictional
   Orion request, then resolve its connected-test gate. No new human decision is
   needed for the remaining local engineering work.

No production readiness, usable model quota, real response latency, actual
cancellation, or subscription inference success is claimed. No push performed.

## Sources

The installed CLI-generated `TurnCompletedNotification` schema supplies the
camel-case `codexErrorInfo` variants used in failure classification. Official
[App Server documentation](https://learn.chatgpt.com/docs/app-server) describes
the effective configuration read and event protocol. The official
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents feature, app/MCP and sandbox controls. Local effective reads were used
to check compatibility with this installed build rather than assuming examples
were sufficient.
