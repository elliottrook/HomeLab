# F2 observer launcher inactive-install review — 2026-10-26

**Decision:** GO for one separately approved inactive installation only.

Stream A reviewed the platform card at full commit
`a46b004f94fc7d4a3fd4038125615266b8c8b564`. Card SHA-256 is
`b743c8398b33037e01db7c9200c167f769417d51386c72891fc1e19f9955eb4c`.

The card is internally consistent with live read-only prestate:

- installed predecessor SHA-256 `9efe6e5d…e8a1`, `root:root 0644`, one link;
- replacement SHA-256 `6a1d520a…8193` from source commit `d00073e5`;
- regression SHA-256 `2a21d242…032a`;
- October 26 terminal-state SHA-256 `51e296ea…de6`, `root:root 0600`, one link;
- recurring F2 timers disabled and inactive.

The transaction replaces one installed Python file, checkpoints the exact
predecessor, verifies the real default Popen contract through the installed
module, requires the 15-test focused and 51-test broader target-Linux suites,
and preserves the spent-cycle evidence. Rollback restores only the predecessor.

The card explicitly excludes timer activation, F2 retry, archive scanning,
receipt creation, lease acquisition, service stops and model calls. Passing the
installation does not authorize a new cycle. Host mutation remains blocked on
Jason's explicit approval of this exact card.
