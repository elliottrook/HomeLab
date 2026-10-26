# D4 candidate-H inactive staging attempt 1 — 2026-10-25

**Result:** NO-GO; automatic rollback verified

The approved source-only bundle reached LXC104 with staging archive SHA-256
`10ae11d271c18747b673f5224f74e052df4edbde94f8c790033e1318357ea469`.
Preflight proved UID/GID 977, the dedicated identity, both directories and all
three persistent control targets were absent. Aster Agent was active and the
existing credential file was root:aster mode 0640.

The inactive installer created the fixed identity and files, left the oneshot
unit inactive and reached the content-free validator. The validator stopped
before invoking its fictional child because Python's generic
`spec_from_file_location` returned no loader for the extensionless installed
launcher path. No credential was opened, no journal was created, no service was
started and no model request ran.

The bounded failure trap removed:

- `/run/aster-d4-candidate-h-target-validation`;
- the candidate unit and launcher;
- both candidate directories;
- the sysusers fragment; and
- user/group and UID/GID 977.

Independent read-only postcheck proved every target and identity absent, Aster
Agent active and `/etc/aster/aster.env` still root:aster mode 0640.

The replacement validator uses `SourceFileLoader` explicitly and adds a
regression that imports an extensionless source path. Its four tests pass and
its SHA-256 is
`e38952b4495326b12e37b0b23f17bc8c061d03ccefda1af71ad390d34186e7a5`.
The corrected bundle must pass its complete local validation before a separately
approved retry.
