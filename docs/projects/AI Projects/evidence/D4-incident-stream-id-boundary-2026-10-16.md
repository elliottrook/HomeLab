# D4 incident reconnect presentation — identifier boundary

**State:** offline candidate only; no gateway route, connected Codex tool or
permission change.

The incident contract allows a caller-supplied `incident_id` of up to 80
characters. The presentation-only reconnect stream previously copied it into
both its progress and incident frames. That could expose private wording if an
upstream caller used descriptive text as the identifier. The internal store
still uses the ID for authenticated lookup; the UI frames do not need it.

The candidate now omits the ID from both frames. A synthetic test puts a
private marker into the snapshot ID and confirms it is absent from the
presentation; another confirms the stored fixture ID is absent from the full
reconnect stream. The focused investigation/store/stream suite passed 19/19.
The separate FastAPI gateway test was not run because this checkout's system
Python lacks `fastapi`; no dependency was installed for this offline edit.
This is a privacy boundary check, not evidence of a deployed SSE route or a
useful read-only sysadmin diagnosis. Any later route must independently bind
its reconnect request to an authorized caller and incident.
