# D4 next-step presentation boundary — offline candidate

The offline incident SSE adapter previously copied the persisted `next` dict
into the UI response and replaced only its `reason`. A future producer field,
or an unexpected persisted field, could therefore appear in a presentation
frame without a privacy review. The incident title, facts and hypotheses were
already excluded.

The local candidate now constructs the next step from known state, registered
target/kind and fixed explanatory text. It rejects an unknown state or
unregistered route. Synthetic tests inject private extra, execution and reason
fields; none reaches the rendered frame. Terminal states retain concise fixed
wording. The incident stream and store focused suites pass 16/16 on the Mac.

This is source-only. No SSE endpoint, connected diagnostic tool, model egress,
AI-PAM grant or live incident reader was deployed or enabled. M1 and D4
qualification gates remain open.
