# Sanitized Doctor observations

This directory accepts one runtime observation per deployed appliance, named
`<device-id>.json`. Observations are evidence, never desired state. They may
contain only resource identifiers, hashes, modes, dependency availability,
typed assertion results and an offset-qualified `observed_at` timestamp.

Never store credentials, account content, media history, camera images or raw
configuration here. Doctor fails closed when evidence is missing, older than
24 hours, from the future, malformed, identity-mismatched or composition-stale.
